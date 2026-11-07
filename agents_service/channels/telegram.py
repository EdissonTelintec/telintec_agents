# -*- coding: utf-8 -*-
"""Canal Telegram del agente virtual de ventas (F2, docs/agentes_openai.md del API, D13).

- Bot `@telintec_AI_bot` (`TELEGRAM_TOKEN`). Webhook `POST /agents/sales/telegram` con el encabezado
  `X-Telegram-Bot-Api-Secret-Token` (prod) o polling con `scripts/telegram_polling.py` (dev).
- Cada chat de Telegram es una conversacion del Store (`channel` 1, `user_ref` `telegram:<user_id>`);
  `/start` o 24 h sin mensajes abren una nueva y cierran la anterior.
- La respuesta del agente (markdown) se convierte a HTML de Telegram; las fotos van como enlace.
"""

from __future__ import annotations

import html
import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
from agents import Agent
from chatkit.agents import AgentContext
from chatkit.types import ClosedStatus, ThreadMetadata

from agents_service.config import Settings
from agents_service.context import AGENT_SALES, CHANNEL_TELEGRAM, RequestContext
from agents_service.limits import Limits
from agents_service.store import MySQLStore
from agents_service.turn import run_turn

log = logging.getLogger("agents.telegram")

TELEGRAM_MAX_LEN = 4096
START_TEXT = (
    "¡Hola! Soy Robotín, el agente virtual de Telintec. Te ayudo a encontrar productos de redes, "
    "seguridad y telecomunicaciones, te cuento de nuestros servicios y, si quieres, levanto una "
    "solicitud de cotización para que un asesor te contacte. ¿Qué estás buscando?"
)
UNSUPPORTED_TEXT = "Por ahora solo puedo leer texto. Escríbeme qué producto o servicio buscas."


class TelegramClient:
    """Lo minimo de la Bot API que usa el canal, con httpx."""

    def __init__(self, token: str, timeout: float = 35.0):
        self._base = f"https://api.telegram.org/bot{token}"
        self._http = httpx.AsyncClient(timeout=timeout)

    async def close(self) -> None:
        await self._http.aclose()

    async def _call(self, method: str, **params: Any) -> Any:
        r = await self._http.post(f"{self._base}/{method}", json={k: v for k, v in params.items() if v is not None})
        data = r.json()
        if not data.get("ok"):
            raise RuntimeError(f"Telegram {method}: {data.get('description')}")
        return data.get("result")

    async def get_me(self) -> dict[str, Any]:
        return await self._call("getMe")

    async def get_updates(self, offset: int | None, timeout: int = 30) -> list[dict[str, Any]]:
        return await self._call("getUpdates", offset=offset, timeout=timeout, allowed_updates=["message"])

    async def send_message(self, chat_id: int, text: str, parse_mode: str | None = "HTML") -> Any:
        return await self._call("sendMessage", chat_id=chat_id, text=text, parse_mode=parse_mode, disable_web_page_preview=False)

    async def send_chat_action(self, chat_id: int, action: str = "typing") -> Any:
        return await self._call("sendChatAction", chat_id=chat_id, action=action)

    async def get_webhook_info(self) -> dict[str, Any]:
        return await self._call("getWebhookInfo")

    async def set_webhook(self, url: str, secret_token: str) -> Any:
        return await self._call("setWebhook", url=url, secret_token=secret_token, allowed_updates=["message"], drop_pending_updates=True)

    async def delete_webhook(self) -> Any:
        return await self._call("deleteWebhook", drop_pending_updates=False)


def markdown_to_telegram_html(text: str) -> str:
    """Markdown del agente -> HTML que acepta Telegram (b, i, code, a). Las imagenes van como enlace."""
    out: list[str] = []
    for line in text.splitlines():
        line = html.escape(line, quote=False)
        line = re.sub(r"!\[([^\]]*)\]\((https?://[^)\s]+)\)", lambda m: f'<a href="{m.group(2)}">📷 {m.group(1) or "foto"}</a>', line)
        line = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", r'<a href="\2">\1</a>', line)
        line = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", line)
        line = re.sub(r"`([^`]+)`", r"<code>\1</code>", line)
        heading = re.match(r"^\s*#{1,6}\s+(.*)$", line)
        if heading:
            line = f"<b>{heading.group(1)}</b>"
        line = re.sub(r"^(\s*)[-*]\s+", r"\1• ", line)
        out.append(line)
    return "\n".join(out).strip()


def split_message(text: str, limit: int = TELEGRAM_MAX_LEN) -> list[str]:
    parts: list[str] = []
    while len(text) > limit:
        cut = text.rfind("\n", 0, limit)
        cut = cut if cut > limit // 2 else limit
        parts.append(text[:cut])
        text = text[cut:].lstrip("\n")
    parts.append(text)
    return parts


def parse_message(update: dict[str, Any]) -> tuple[int, int, str | None, str | None] | None:
    """(chat_id, user_id, texto, nombre) del update, o None si no trae mensaje."""
    msg = update.get("message") or update.get("edited_message")
    if not msg or "chat" not in msg:
        return None
    chat_id = int(msg["chat"]["id"])
    sender = msg.get("from") or {}
    user_id = int(sender.get("id") or chat_id)
    name = " ".join(x for x in (sender.get("first_name"), sender.get("last_name")) if x) or sender.get("username")
    return chat_id, user_id, msg.get("text"), name


class TelegramChannel:
    def __init__(
        self,
        client: TelegramClient,
        store: MySQLStore,
        limits: Limits,
        settings: Settings,
        agent: Agent[AgentContext],
        fixed_text,
        session_hours: int = 24,
    ):
        self.client = client
        self.store = store
        self.limits = limits
        self.settings = settings
        self.agent = agent
        self.fixed_text = fixed_text
        self.session = timedelta(hours=session_hours)

    @staticmethod
    def context_for(user_id: int) -> RequestContext:
        return RequestContext(agent=AGENT_SALES, channel=CHANNEL_TELEGRAM, user_ref=f"telegram:{user_id}")

    async def resolve_conversation(self, context: RequestContext, reset: bool = False) -> ThreadMetadata:
        """La conversacion abierta del usuario, o una nueva si no hay, si pidio /start o si lleva 24 h callada."""
        page = await self.store.load_threads(limit=1, after=None, order="desc", context=context)
        current = page.data[0] if page.data else None
        if current is not None and current.status.type == "active" and not reset:
            last = await self.store.last_activity(current.id)
            if last is not None and datetime.now(timezone.utc) - last < self.session:
                return current
        if current is not None and current.status.type == "active":
            current.status = ClosedStatus(reason="nueva conversación" if reset else "inactividad")
            await self.store.save_thread(current, context)
        thread = ThreadMetadata(id=self.store.generate_thread_id(context), created_at=datetime.now(timezone.utc))
        await self.store.save_thread(thread, context)
        return thread

    async def handle_update(self, update: dict[str, Any]) -> str | None:
        """Procesa un update y manda la respuesta. Devuelve el texto enviado (para pruebas)."""
        parsed = parse_message(update)
        if parsed is None:
            return None
        chat_id, user_id, text, _name = parsed
        try:
            if not text:
                await self.client.send_message(chat_id, UNSUPPORTED_TEXT, parse_mode=None)
                return UNSUPPORTED_TEXT
            context = self.context_for(user_id)
            if text.strip().lower().startswith("/start"):
                await self.resolve_conversation(context, reset=True)
                await self.client.send_message(chat_id, START_TEXT, parse_mode=None)
                return START_TEXT
            thread = await self.resolve_conversation(context)
            await self.client.send_chat_action(chat_id, "typing")
            reply = await run_turn(self.store, self.limits, self.agent, thread, context, text.strip(), self.fixed_text)
            for part in split_message(markdown_to_telegram_html(reply)):
                await self.client.send_message(chat_id, part)
            return reply
        except Exception as e:  # noqa: BLE001 - nunca dejar al usuario sin respuesta
            log.exception("telegram chat %s: %s", chat_id, e)
            try:
                await self.client.send_message(chat_id, self.fixed_text("error"), parse_mode=None)
            except Exception:  # noqa: BLE001
                pass
            return None

    async def poll_forever(self, timeout: int = 30) -> None:
        """Long polling (dev). Falla si el bot tiene webhook: Telegram no permite las dos cosas."""
        info = await self.client.get_webhook_info()
        if info.get("url"):
            raise RuntimeError(f"el bot tiene webhook configurado ({info['url']}); polling no disponible. Borrarlo solo si ya no lo usa nadie.")
        offset: int | None = None
        log.info("polling de Telegram iniciado")
        while True:
            try:
                updates = await self.client.get_updates(offset, timeout=timeout)
            except Exception as e:  # noqa: BLE001
                log.warning("getUpdates fallo: %s", e)
                continue
            for update in updates:
                offset = int(update["update_id"]) + 1
                await self.handle_update(update)
