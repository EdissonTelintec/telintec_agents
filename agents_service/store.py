# -*- coding: utf-8 -*-
"""Store de ChatKit sobre MySQL (`sql_telintec_mod_agents`).

- `agent_conversations` guarda la ThreadMetadata: `title` y `chatkit_meta` (status, metadata,
  allowed_image_domains) son de ChatKit; `agent`, `channel`, `user_ref`, `ip_hash` y
  `page_context` salen del RequestContext al crear la conversacion; `status` es el de negocio
  (0 abierta, 1 cerrada, 2 revisada): ChatKit lo lleva a 1 cuando bloquea o cierra el hilo y
  nunca baja un 2.
- `agent_messages` guarda cada item tal cual (`payload` JSON) con `seq` por conversacion.
- Adjuntos: deshabilitados (el widget no los ofrece).
- Dueno de la conversacion (P-260): toda operacion por id exige el mismo agente y canal y, si el contexto
  trae identidad (`user_ref`), el mismo dueno; el visitante web no tiene identidad, asi que su llave es el
  id de 128 bits que solo tiene su navegador (los ids cortos de antes no se le sirven). Una conversacion
  ajena se responde igual que una inexistente: ThreadNotFound al leer o escribir, nada al borrar.
- Ids de conversacion y de mensaje de 128 bits (`new_id`): los de ChatKit traen 8 hex, adivinables y con
  choques en la PK global de `agent_messages`.

Las fechas se guardan en hora local del servicio (`SERVICE_TIMEZONE`, America/Mexico_City) naive, como el
resto del esquema y el API, y se devuelven con esa tzinfo. Un datetime naive se toma como hora del sistema
(ChatKit usa `datetime.now()`; prod corre con TZ=America/Mexico_City); uno con tzinfo se convierte.
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from chatkit.store import Store, StoreItemType, default_generate_id
from chatkit.types import Attachment, Page, ThreadItem, ThreadMetadata, ThreadStatus
from pydantic import TypeAdapter

from agents_service.context import RequestContext
from agents_service.db import Database

STATUS_OPEN = 0
STATUS_CLOSED = 1
STATUS_REVIEWED = 2

_item_adapter: TypeAdapter[ThreadItem] = TypeAdapter(ThreadItem)
_status_adapter: TypeAdapter[ThreadStatus] = TypeAdapter(ThreadStatus)


class ThreadNotFound(LookupError):
    pass


class ItemNotFound(LookupError):
    pass


DEFAULT_TIMEZONE = "America/Mexico_City"


def _to_db(dt: datetime, tz: ZoneInfo) -> datetime:
    """A hora local del servicio, naive. `astimezone` en un naive lo toma como hora del sistema."""
    return dt.astimezone(tz).replace(tzinfo=None)


def _from_db(dt: datetime, tz: ZoneInfo) -> datetime:
    return dt.replace(tzinfo=tz) if dt.tzinfo is None else dt


# ---- dueno de la conversacion (P-260) ------------------------------------

ID_HEX_LEN = 32  # uuid4 completo = 128 bits; el id por defecto de ChatKit trae 8 hex (32 bits)

log = logging.getLogger("agents.store")


def new_id(item_type: StoreItemType) -> str:
    """Id de 128 bits con el prefijo de ChatKit (thr_, msg_...): no se adivina y no choca en la PK global."""
    prefix = default_generate_id(item_type).rsplit("_", 1)[0]
    return f"{prefix}_{uuid.uuid4().hex}"


def is_short_id(conversation_id: str) -> bool:
    """Id de antes de P-260 (8 hex despues del prefijo) o hecho a mano: adivinable."""
    return len(conversation_id.rsplit("_", 1)[-1]) < ID_HEX_LEN


def is_owner(agent: int, channel: int, user_ref: str | None, conversation_id: str, context: RequestContext) -> bool:
    """Regla del dueno de la conversacion: mismo agente y canal siempre; con identidad (empleado, usuario de
    Telegram) el mismo `user_ref`; sin identidad (visitante web), una conversacion sin dueno identificado y con
    id de 128 bits, la llave que solo tiene su navegador."""
    if agent != context.agent or channel != context.channel:
        return False
    if context.user_ref:
        return user_ref == context.user_ref
    return user_ref is None and not is_short_id(conversation_id)


def log_denied(context: RequestContext) -> None:
    """Rastro de un intento sobre una conversacion ajena; sin ids ni datos personales."""
    log.warning(
        "Conversacion ajena respondida como inexistente (agente %s, canal %s, con identidad: %s)",
        context.agent,
        context.channel,
        bool(context.user_ref),
    )


# Candado del upsert de save_thread: solo el dueno actualiza una fila que ya existe.
_SAME_OWNER = (
    "agent_conversations.agent = new.agent AND agent_conversations.channel = new.channel "
    "AND agent_conversations.user_ref <=> new.user_ref"
)


class MySQLStore(Store[RequestContext]):
    def __init__(self, db: Database, schema: str = "sql_telintec_mod_agents", timezone: str = DEFAULT_TIMEZONE):
        self._db = db
        self._tz = ZoneInfo(timezone)
        self._conv = f"{schema}.agent_conversations"
        self._msg = f"{schema}.agent_messages"

    # ---- conversaciones --------------------------------------------------

    def _row_to_thread(self, row: dict[str, Any]) -> ThreadMetadata:
        meta = json.loads(row["chatkit_meta"]) if row.get("chatkit_meta") else {}
        return ThreadMetadata(
            id=row["conversation_id"],
            created_at=_from_db(row["created_at"], self._tz),
            title=row.get("title"),
            status=_status_adapter.validate_python(meta.get("status") or {"type": "active"}),
            allowed_image_domains=meta.get("allowed_image_domains"),
            metadata=meta.get("metadata") or {},
        )

    def generate_thread_id(self, context: RequestContext) -> str:
        return new_id("thread")

    def generate_item_id(self, item_type: StoreItemType, thread: ThreadMetadata, context: RequestContext) -> str:
        return new_id(item_type)

    async def _fetch_conversation(self, thread_id: str) -> dict[str, Any] | None:
        return await self._db.fetch_one(
            f"SELECT conversation_id, created_at, title, chatkit_meta, agent, channel, user_ref FROM {self._conv} "
            "WHERE conversation_id = %s",
            (thread_id,),
        )

    async def _owned(self, thread_id: str, context: RequestContext) -> dict[str, Any]:
        """La fila de la conversacion si `context` es su dueno. Inexistente o ajena -> ThreadNotFound, igual en
        los dos casos para no confirmar que el id existe."""
        row = await self._fetch_conversation(thread_id)
        if row is None:
            raise ThreadNotFound(thread_id)
        if not is_owner(row["agent"], row["channel"], row["user_ref"], thread_id, context):
            log_denied(context)
            raise ThreadNotFound(thread_id)
        return row

    async def load_thread(self, thread_id: str, context: RequestContext) -> ThreadMetadata:
        return self._row_to_thread(await self._owned(thread_id, context))

    async def save_thread(self, thread: ThreadMetadata, context: RequestContext) -> None:
        existing = await self._fetch_conversation(thread.id)
        if existing is not None and not is_owner(
            existing["agent"], existing["channel"], existing["user_ref"], thread.id, context
        ):
            log_denied(context)
            raise ThreadNotFound(thread.id)
        meta = json.dumps(
            {
                "status": thread.status.model_dump(mode="json"),
                "metadata": thread.metadata,
                "allowed_image_domains": thread.allowed_image_domains,
            },
            ensure_ascii=False,
        )
        business_status = STATUS_OPEN if thread.status.type == "active" else STATUS_CLOSED
        await self._db.execute(
            f"INSERT INTO {self._conv} "
            "(conversation_id, agent, channel, user_ref, ip_hash, page_context, title, chatkit_meta, status, created_at) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) AS new "  # alias `new`: MySQL >= 8.0.19
            # el candado repite la regla de arriba en el mismo UPDATE (si otro gana la carrera, no se pisa)
            "ON DUPLICATE KEY UPDATE "
            f"title = IF({_SAME_OWNER}, new.title, agent_conversations.title), "
            f"chatkit_meta = IF({_SAME_OWNER}, new.chatkit_meta, agent_conversations.chatkit_meta), "
            f"status = IF({_SAME_OWNER} AND agent_conversations.status <> 2, new.status, agent_conversations.status)",
            (
                thread.id,
                context.agent,
                context.channel,
                context.user_ref,
                context.ip_hash,
                context.page_context,
                thread.title,
                meta,
                business_status,
                _to_db(thread.created_at, self._tz),
            ),
        )

    async def load_threads(self, limit: int, after: str | None, order: str, context: RequestContext) -> Page[ThreadMetadata]:
        """Solo las conversaciones del mismo usuario y agente; un visitante sin identidad no tiene lista."""
        if not context.user_ref:
            return Page(data=[], has_more=False, after=None)
        desc = order != "asc"
        args: list[Any] = [context.agent, context.user_ref]
        cursor_sql = ""
        if after:
            ref = await self._db.fetch_one(
                f"SELECT created_at FROM {self._conv} WHERE conversation_id = %s", (after,)
            )
            if ref is not None:
                cursor_sql = "AND (created_at, conversation_id) " + ("<" if desc else ">") + " (%s, %s) "
                args += [ref["created_at"], after]
        rows = await self._db.fetch_all(
            f"SELECT conversation_id, created_at, title, chatkit_meta FROM {self._conv} "
            f"WHERE agent = %s AND user_ref = %s {cursor_sql}"
            f"ORDER BY created_at {'DESC' if desc else 'ASC'}, conversation_id {'DESC' if desc else 'ASC'} LIMIT %s",
            args + [limit + 1],
        )
        has_more = len(rows) > limit
        threads = [self._row_to_thread(r) for r in rows[:limit]]
        return Page(data=threads, has_more=has_more, after=threads[-1].id if has_more and threads else None)

    async def delete_thread(self, thread_id: str, context: RequestContext) -> None:
        try:
            await self._owned(thread_id, context)
        except ThreadNotFound:
            return  # inexistente o ajena: nada que borrar, la misma respuesta en los dos casos
        await self._db.execute(f"DELETE FROM {self._conv} WHERE conversation_id = %s", (thread_id,))

    # ---- items -----------------------------------------------------------

    async def load_thread_items(
        self, thread_id: str, after: str | None, limit: int, order: str, context: RequestContext
    ) -> Page[ThreadItem]:
        await self._owned(thread_id, context)
        desc = order == "desc"
        args: list[Any] = [thread_id]
        cursor_sql = ""
        if after:
            ref = await self._db.fetch_one(
                f"SELECT seq FROM {self._msg} WHERE conversation_id = %s AND message_id = %s", (thread_id, after)
            )
            if ref is not None:
                cursor_sql = "AND seq " + ("<" if desc else ">") + " %s "
                args.append(ref["seq"])
        rows = await self._db.fetch_all(
            f"SELECT payload FROM {self._msg} WHERE conversation_id = %s {cursor_sql}"
            f"ORDER BY seq {'DESC' if desc else 'ASC'} LIMIT %s",
            args + [limit + 1],
        )
        has_more = len(rows) > limit
        items = [self._row_to_item(r) for r in rows[:limit]]
        return Page(data=items, has_more=has_more, after=items[-1].id if has_more and items else None)

    @staticmethod
    def _row_to_item(row: dict[str, Any]) -> ThreadItem:
        payload = row["payload"]
        data = json.loads(payload) if isinstance(payload, (str, bytes)) else payload
        return _item_adapter.validate_python(data)

    async def add_thread_item(self, thread_id: str, item: ThreadItem, context: RequestContext) -> None:
        await self._owned(thread_id, context)
        await self._insert_item(thread_id, item)

    async def _insert_item(self, thread_id: str, item: ThreadItem) -> None:
        payload = json.dumps(item.model_dump(mode="json"), ensure_ascii=False)
        await self._db.execute(
            f"INSERT INTO {self._msg} (message_id, conversation_id, seq, item_type, payload, created_at) "
            f"SELECT %s, %s, COALESCE(MAX(seq), 0) + 1, %s, %s, %s FROM {self._msg} WHERE conversation_id = %s",
            (item.id, thread_id, item.type, payload, _to_db(item.created_at, self._tz), thread_id),
        )

    async def save_item(self, thread_id: str, item: ThreadItem, context: RequestContext) -> None:
        await self._owned(thread_id, context)
        exists = await self._db.fetch_one(
            f"SELECT 1 AS x FROM {self._msg} WHERE conversation_id = %s AND message_id = %s", (thread_id, item.id)
        )
        if exists is None:
            await self._insert_item(thread_id, item)
            return
        payload = json.dumps(item.model_dump(mode="json"), ensure_ascii=False)
        await self._db.execute(
            f"UPDATE {self._msg} SET item_type = %s, payload = %s WHERE conversation_id = %s AND message_id = %s",
            (item.type, payload, thread_id, item.id),
        )

    async def load_item(self, thread_id: str, item_id: str, context: RequestContext) -> ThreadItem:
        await self._owned(thread_id, context)
        row = await self._db.fetch_one(
            f"SELECT payload FROM {self._msg} WHERE conversation_id = %s AND message_id = %s", (thread_id, item_id)
        )
        if row is None:
            raise ItemNotFound(item_id)
        return self._row_to_item(row)

    async def delete_thread_item(self, thread_id: str, item_id: str, context: RequestContext) -> None:
        try:
            await self._owned(thread_id, context)
        except ThreadNotFound:
            return  # como delete_thread: inexistente o ajena, nada que borrar
        await self._db.execute(
            f"DELETE FROM {self._msg} WHERE conversation_id = %s AND message_id = %s", (thread_id, item_id)
        )

    async def last_activity(self, thread_id: str) -> datetime | None:
        """Fecha (con tzinfo) del ultimo mensaje de la conversacion, o de su creacion si no hay mensajes."""
        row = await self._db.fetch_one(
            f"SELECT COALESCE(MAX(m.created_at), c.created_at) AS last FROM {self._conv} c "
            f"LEFT JOIN {self._msg} m ON m.conversation_id = c.conversation_id "
            "WHERE c.conversation_id = %s GROUP BY c.conversation_id",
            (thread_id,),
        )
        return _from_db(row["last"], self._tz) if row and row["last"] else None

    async def count_items(self, thread_id: str, item_type: str | None = None) -> int:
        """Mensajes de una conversacion (para el tope por conversacion)."""
        extra = "AND item_type = %s" if item_type else ""
        args: tuple[Any, ...] = (thread_id, item_type) if item_type else (thread_id,)
        row = await self._db.fetch_one(
            f"SELECT COUNT(*) AS n FROM {self._msg} WHERE conversation_id = %s {extra}", args
        )
        return int(row["n"]) if row else 0

    # ---- adjuntos: deshabilitados ---------------------------------------

    async def save_attachment(self, attachment: Attachment, context: RequestContext) -> None:
        raise NotImplementedError("adjuntos deshabilitados")

    async def load_attachment(self, attachment_id: str, context: RequestContext) -> Attachment:
        raise NotImplementedError("adjuntos deshabilitados")

    async def delete_attachment(self, attachment_id: str, context: RequestContext) -> None:
        raise NotImplementedError("adjuntos deshabilitados")
