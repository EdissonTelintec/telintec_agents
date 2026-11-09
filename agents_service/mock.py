# -*- coding: utf-8 -*-
"""Servidor simulado para que el front pruebe su integracion sin OpenAI, sin MySQL y sin tocar prod.

    python scripts/mock_server.py          # http://127.0.0.1:8100/agents

- Mismas rutas y contrato que el servicio: los routers reales (`health`, `sales`, `assistant`), el mismo
  envelope del 401 y el protocolo de ChatKit de la libreria (`ChatKitServer`). Lo que funciona aqui
  funciona contra prod.
- Store en memoria: las conversaciones se pierden al apagar.
- Respuestas guionadas por palabra clave (`SCENARIOS_HELP`), en stream palabra por palabra; los textos
  fijos (tope, fuera de tema, error) llegan en un solo evento, como en el servicio real.
- `Authorization`: JWT crudo ES256 con `exp` e `iat`, vigente y de hasta 24 h. **No verifica la firma ni
  el `kid`**: sirve cualquier token del login. Sin token, con `Bearer`, HS256 o vencido -> el mismo 401.
- CORS: cualquier `http://localhost:<puerto>` o `http://127.0.0.1:<puerto>`, mas los `origins` que se pasen.
- Nunca escribe en la BD, no llama a OpenAI ni avisa a ventas.
"""

from __future__ import annotations

import asyncio
import copy
import unicodedata
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Protocol

import jwt
from chatkit.server import ChatKitServer
from chatkit.store import Store
from chatkit.types import (
    Annotation,
    AssistantMessageContent,
    AssistantMessageContentPartAdded,
    AssistantMessageContentPartAnnotationAdded,
    AssistantMessageContentPartDone,
    AssistantMessageContentPartTextDelta,
    AssistantMessageItem,
    Attachment,
    FileSource,
    Page,
    ThreadItem,
    ThreadItemAddedEvent,
    ThreadItemDoneEvent,
    ThreadItemUpdatedEvent,
    ThreadMetadata,
    ThreadStreamEvent,
    UserMessageItem,
)
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from agents_service.agents import assistant as assistant_texts
from agents_service.agents import sales as sales_texts
from agents_service.auth import UNAUTHORIZED_MSG, TokenError, TokenVerifier, Unauthorized, permission_names
from agents_service.config import Settings, load_settings
from agents_service.context import AGENT_ASSISTANT, AGENT_SALES, RequestContext
from agents_service.knowledge import HelpBase
from agents_service.routers import assistant, health, sales
from agents_service.store import ItemNotFound, ThreadNotFound

LOCAL_ORIGINS = r"http://(localhost|127\.0\.0\.1)(:\d+)?"
PRODUCT_IMAGE_DOMAINS = ["ftp3.syscom.mx"]  # el mismo que main.PRODUCT_IMAGE_DOMAINS
DEFAULT_DELAY = 0.03  # segundos entre palabras del stream

SCENARIOS_HELP = (
    "Escribe una de estas palabras para provocar cada caso: **producto**, **cotización**, **markdown**, "
    "**guía** (asistente), **tope**, **fuera de tema**, **error**."
)

_PRODUCTS = (  # datos de ejemplo: nombres y fotos reales del catalogo, precios inventados
    ("Timbre con cámara Wi-Fi de batería recargable, uso exterior IP65", "EZVIZ", "CS-DB2KIT", "2,450.00", True,
     "https://ftp3.syscom.mx/usuarios/fotos/BancoFotografiasSyscom/EZVIZ/CSDB2KIT/CSDB2KIT-p.PNG"),
    ("Switch PoE+ no administrable de 10 puertos, 110 W", "HIKVISION", "DS-3E0310HP-E", "2,180.00", True,
     "https://ftp3.syscom.mx/usuarios/fotos/BancoFotografiasSyscom/HIKVISION/DS3E0310HPE/DS3E0310HPE-p.PNG"),
    ("Access Point UniFi doble banda 802.11ac, interior, PoE", "UBIQUITI NETWORKS", "UAP-AC-LITE", "2,390.00", False,
     "https://ftp3.syscom.mx/usuarios/fotos/BancoFotografiasSyscom/UBIQUITINETWORKS/UAPACLITE/UAPACLITE-p.PNG"),
)

_MARKDOWN_SAMPLE = """## Ejemplo de formato

Texto con **negritas**, *cursivas* y `código`.

1. Una lista numerada
2. Con dos pasos

- Una viñeta
- Otra con un [enlace](https://telintec.mx)

| Columna | Valor |
|---|---|
| uno | 1 |
| dos | 2 |

> Una cita al final."""


# ---- Store en memoria -----------------------------------------------------


@dataclass
class _Thread:
    meta: ThreadMetadata
    agent: int
    user_ref: str | None
    items: list[ThreadItem] = field(default_factory=list)


class MemoryStore(Store[RequestContext]):
    """Store de ChatKit en un dict: mismas reglas de visibilidad que `MySQLStore` (la lista de
    conversaciones es del mismo usuario y agente; un visitante sin identidad no tiene lista)."""

    def __init__(self) -> None:
        self._threads: dict[str, _Thread] = {}

    def _get(self, thread_id: str) -> _Thread:
        thread = self._threads.get(thread_id)
        if thread is None:
            raise ThreadNotFound(thread_id)
        return thread

    async def load_thread(self, thread_id: str, context: RequestContext) -> ThreadMetadata:
        return self._get(thread_id).meta.model_copy(deep=True)

    async def save_thread(self, thread: ThreadMetadata, context: RequestContext) -> None:
        # ChatKit a veces pasa un `Thread` (con sus items): se guarda solo la metadata, como MySQLStore
        meta = ThreadMetadata.model_validate(thread.model_dump(include=set(ThreadMetadata.model_fields)))
        existing = self._threads.get(thread.id)
        if existing is None:
            self._threads[thread.id] = _Thread(meta, context.agent, context.user_ref)
        else:
            existing.meta = meta

    async def load_threads(self, limit: int, after: str | None, order: str, context: RequestContext) -> Page[ThreadMetadata]:
        if not context.user_ref:
            return Page(data=[], has_more=False, after=None)
        mine = [t.meta for t in self._threads.values() if t.agent == context.agent and t.user_ref == context.user_ref]
        mine.sort(key=lambda m: (m.created_at, m.id), reverse=order != "asc")
        return _page(mine, after, limit)

    async def delete_thread(self, thread_id: str, context: RequestContext) -> None:
        self._threads.pop(thread_id, None)

    async def load_thread_items(
        self, thread_id: str, after: str | None, limit: int, order: str, context: RequestContext
    ) -> Page[ThreadItem]:
        items = list(self._get(thread_id).items)
        if order == "desc":
            items.reverse()
        return _page(items, after, limit)

    async def add_thread_item(self, thread_id: str, item: ThreadItem, context: RequestContext) -> None:
        self._get(thread_id).items.append(copy.deepcopy(item))

    async def save_item(self, thread_id: str, item: ThreadItem, context: RequestContext) -> None:
        items = self._get(thread_id).items
        for i, existing in enumerate(items):
            if existing.id == item.id:
                items[i] = copy.deepcopy(item)
                return
        items.append(copy.deepcopy(item))

    async def load_item(self, thread_id: str, item_id: str, context: RequestContext) -> ThreadItem:
        for item in self._get(thread_id).items:
            if item.id == item_id:
                return copy.deepcopy(item)
        raise ItemNotFound(item_id)

    async def delete_thread_item(self, thread_id: str, item_id: str, context: RequestContext) -> None:
        thread = self._get(thread_id)
        thread.items = [i for i in thread.items if i.id != item_id]

    async def save_attachment(self, attachment: Attachment, context: RequestContext) -> None:
        raise NotImplementedError("adjuntos deshabilitados")

    async def load_attachment(self, attachment_id: str, context: RequestContext) -> Attachment:
        raise NotImplementedError("adjuntos deshabilitados")

    async def delete_attachment(self, attachment_id: str, context: RequestContext) -> None:
        raise NotImplementedError("adjuntos deshabilitados")


class _HasId(Protocol):
    id: str


def _page[T: _HasId](rows: list[T], after: str | None, limit: int) -> Page[T]:
    if after:
        ids = [r.id for r in rows]
        rows = rows[ids.index(after) + 1:] if after in ids else rows
    data = rows[:limit]
    has_more = len(rows) > limit
    return Page(data=data, has_more=has_more, after=data[-1].id if has_more and data else None)


# ---- Token sin firma ------------------------------------------------------


class UnsignedTokenVerifier(TokenVerifier):
    """Como `TokenVerifier` (ES256, `exp` + `iat`, vigente, <= 24 h) pero sin verificar firma ni `kid`."""

    def __init__(self, leeway_seconds: int = 30, max_lifetime_seconds: int = 24 * 60 * 60):
        super().__init__(Path("."), (), leeway_seconds, max_lifetime_seconds)

    def verify(self, token: str) -> dict:
        try:
            header = jwt.get_unverified_header(token)
        except jwt.PyJWTError as e:
            raise TokenError(f"token mal formado: {e}") from e
        if header.get("alg") != "ES256":
            raise TokenError("solo se aceptan tokens ES256")
        try:
            data = jwt.decode(
                token,
                options={"verify_signature": False, "verify_exp": True, "verify_iat": True, "require": ["exp", "iat"]},
                leeway=self._leeway,
            )
        except jwt.PyJWTError as e:
            raise TokenError(str(e)) from e
        if data["exp"] - data["iat"] > self._max_lifetime:
            raise TokenError("token con vigencia de mas de 24 h")
        return data


# ---- Respuestas guionadas -------------------------------------------------


@dataclass(frozen=True)
class Reply:
    text: str
    fixed: bool = False  # texto fijo del servicio (tope, fuera de tema, error): un solo evento, sin stream
    annotations: tuple[Annotation, ...] = ()


def _normalize(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", text.lower())
    return "".join(c for c in decomposed if unicodedata.category(c) != "Mn")


def _fixed_kind(text: str) -> str | None:
    if "fuera de tema" in text:
        return "off_topic"
    if "tope" in text or "limite" in text:
        return "limit"
    if "error" in text:
        return "error"
    return None


def sales_reply(text: str, settings: Settings) -> Reply:
    t = _normalize(text)
    kind = _fixed_kind(t)
    if kind:
        return Reply(sales_texts.fixed_text(kind, settings), fixed=True)
    if "cotiza" in t:
        return Reply(
            "¡Listo! Registré tu solicitud de cotización con el folio **SIM-0001**. Un asesor de ventas te contacta "
            "en horario hábil.\n\n*(Simulación: no se guardó nada ni se avisó a ventas.)*"
        )
    if "producto" in t:
        lines = [
            f"- **{name}** · {brand} · {model} · ${price} MXN · {'disponible' if available else 'sin existencia'}\n"
            f"  ![{model}]({image})"
            for name, brand, model, price, available, image in _PRODUCTS
        ]
        return Reply(
            "Encontré estas opciones *(datos de ejemplo)*:\n\n" + "\n".join(lines)
            + "\n\nLos precios son de lista en MXN con IVA, sujetos a confirmación del asesor. "
            "¿Quieres que te cotice alguno?"
        )
    if "markdown" in t:
        return Reply(_MARKDOWN_SAMPLE)
    return Reply(f"Hola, soy **Robotín** *(simulado)*. Recibí: «{text.strip()}».\n\n{SCENARIOS_HELP}")


def assistant_reply(text: str, context: RequestContext, help_base: HelpBase, settings: Settings) -> Reply:
    t = _normalize(text)
    kind = _fixed_kind(t)
    if kind:
        return Reply(assistant_texts.fixed_text(kind, settings), fixed=True)
    if "markdown" in t:
        return Reply(_MARKDOWN_SAMPLE)
    token = context.token_data
    doc = help_base.module_for_route(context.page_context)
    screen = context.page_context or "(sin `X-Page-Context`)"
    module = f"{doc.title} (`{doc.slug}.md`)" if doc else "ninguna guía cubre esta ruta"
    perms = ", ".join(f"`{p}`" for p in permission_names(token)) or "(ninguno)"
    head = (
        f"Hola, **{token.get('name') or token.get('user')}** *(asistente simulado)*. Esto es lo que me llegó:\n\n"
        f"- **Usuario:** {token.get('user')} · emp_id {token.get('emp_id')}\n"
        f"- **Pantalla:** {screen} → {module}\n"
        f"- **Permisos:** {perms}"
    )
    if "guia" in t and doc:
        body = head + f"\n\nSegún la guía de {doc.title}: {doc.summary}"
        source = FileSource(filename=f"{doc.slug}.md", title=doc.title)
        return Reply(body, annotations=(Annotation(source=source, index=len(body)),))
    return Reply(head + f"\n\n{SCENARIOS_HELP}")


# ---- Servidor de ChatKit simulado -----------------------------------------


class MockChatKitServer(ChatKitServer[RequestContext]):
    def __init__(
        self,
        store: MemoryStore,
        agent: int,
        settings: Settings,
        help_base: HelpBase,
        delay: float = DEFAULT_DELAY,
        allowed_image_domains: list[str] | None = None,
    ):
        super().__init__(store)
        self.agent = agent
        self.settings = settings
        self.help_base = help_base
        self.delay = delay
        self.allowed_image_domains = allowed_image_domains or []

    def reply_for(self, text: str, context: RequestContext) -> Reply:
        if self.agent == AGENT_ASSISTANT:
            return assistant_reply(text, context, self.help_base, self.settings)
        return sales_reply(text, self.settings)

    async def respond(
        self, thread: ThreadMetadata, input_user_message: UserMessageItem | None, context: RequestContext
    ) -> AsyncIterator[ThreadStreamEvent]:
        if self.allowed_image_domains and not thread.allowed_image_domains:
            thread.allowed_image_domains = list(self.allowed_image_domains)
            await self.store.save_thread(thread, context)
        text = " ".join(c.text for c in input_user_message.content) if input_user_message else ""
        reply = self.reply_for(text, context)
        item = AssistantMessageItem(
            id=self.store.generate_item_id("message", thread, context),
            thread_id=thread.id,
            created_at=datetime.now(),
            content=[],
        )
        final = AssistantMessageContent(text=reply.text, annotations=list(reply.annotations))
        if reply.fixed:  # como TelintecChatKitServer._message
            yield ThreadItemDoneEvent(item=item.model_copy(update={"content": [final]}))
            return
        yield ThreadItemAddedEvent(item=item)
        yield ThreadItemUpdatedEvent(
            item_id=item.id, update=AssistantMessageContentPartAdded(content_index=0, content=AssistantMessageContent(text=""))
        )
        words = reply.text.split(" ")
        for i, word in enumerate(words):
            if self.delay:
                await asyncio.sleep(self.delay)
            delta = word if i == len(words) - 1 else word + " "
            yield ThreadItemUpdatedEvent(item_id=item.id, update=AssistantMessageContentPartTextDelta(content_index=0, delta=delta))
        for n, annotation in enumerate(reply.annotations):
            yield ThreadItemUpdatedEvent(
                item_id=item.id,
                update=AssistantMessageContentPartAnnotationAdded(content_index=0, annotation_index=n, annotation=annotation),
            )
        yield ThreadItemUpdatedEvent(item_id=item.id, update=AssistantMessageContentPartDone(content_index=0, content=final))
        yield ThreadItemDoneEvent(item=item.model_copy(update={"content": [final]}))


# ---- App ------------------------------------------------------------------


def load_settings_for_mock() -> Settings:
    """Settings con valores por defecto (WhatsApp y correo de ventas reales); ignora cualquier `.env`."""
    environ = {"AGENTS_ENVIRONMENT": "dev", "DB_HOST": "simulado", "DB_USER": "simulado", "DB_PASSWORD": "simulado"}
    return load_settings(env_file=Path(__file__).with_name("__sin_env__"), environ=environ)


def create_mock_app(delay: float = DEFAULT_DELAY, origins: tuple[str, ...] = ()) -> FastAPI:
    settings = load_settings_for_mock()
    help_base = HelpBase.load()
    store = MemoryStore()

    app = FastAPI(title="Telintec agents (simulado)", docs_url=None, redoc_url=None)
    app.state.settings = settings
    app.state.verifier = UnsignedTokenVerifier(settings.token_leeway_seconds, settings.token_max_lifetime_seconds)
    app.state.help_base = help_base
    app.state.telegram_channel = None
    app.state.sales_server = MockChatKitServer(
        store, AGENT_SALES, settings, help_base, delay, allowed_image_domains=PRODUCT_IMAGE_DOMAINS
    )
    app.state.assistant_server = MockChatKitServer(store, AGENT_ASSISTANT, settings, help_base, delay)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(origins),
        allow_origin_regex=LOCAL_ORIGINS,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Page-Context"],
        max_age=600,
    )

    @app.exception_handler(Unauthorized)
    async def _unauthorized(_: Request, exc: Unauthorized) -> JSONResponse:
        return JSONResponse({"data": None, "msg": UNAUTHORIZED_MSG, "error": exc.error}, status_code=401)

    app.include_router(health.router, prefix="/agents")
    app.include_router(sales.router, prefix="/agents/sales")
    app.include_router(assistant.router, prefix="/agents/assistant")
    return app
