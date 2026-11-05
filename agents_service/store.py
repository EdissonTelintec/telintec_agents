# -*- coding: utf-8 -*-
"""Store de ChatKit sobre MySQL (`sql_telintec_mod_agents`).

- `agent_conversations` guarda la ThreadMetadata: `title` y `chatkit_meta` (status, metadata,
  allowed_image_domains) son de ChatKit; `agent`, `channel`, `user_ref`, `ip_hash` y
  `page_context` salen del RequestContext al crear la conversacion; `status` es el de negocio
  (0 abierta, 1 cerrada, 2 revisada): ChatKit lo lleva a 1 cuando bloquea o cierra el hilo y
  nunca baja un 2.
- `agent_messages` guarda cada item tal cual (`payload` JSON) con `seq` por conversacion.
- Adjuntos: deshabilitados (el widget no los ofrece).

Las fechas se guardan en UTC naive (DATETIME) y se devuelven con tzinfo UTC.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from chatkit.store import Store
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


def _to_db(dt: datetime) -> datetime:
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def _from_db(dt: datetime) -> datetime:
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt


class MySQLStore(Store[RequestContext]):
    def __init__(self, db: Database, schema: str = "sql_telintec_mod_agents"):
        self._db = db
        self._conv = f"{schema}.agent_conversations"
        self._msg = f"{schema}.agent_messages"

    # ---- conversaciones --------------------------------------------------

    @staticmethod
    def _row_to_thread(row: dict[str, Any]) -> ThreadMetadata:
        meta = json.loads(row["chatkit_meta"]) if row.get("chatkit_meta") else {}
        return ThreadMetadata(
            id=row["conversation_id"],
            created_at=_from_db(row["created_at"]),
            title=row.get("title"),
            status=_status_adapter.validate_python(meta.get("status") or {"type": "active"}),
            allowed_image_domains=meta.get("allowed_image_domains"),
            metadata=meta.get("metadata") or {},
        )

    async def load_thread(self, thread_id: str, context: RequestContext) -> ThreadMetadata:
        row = await self._db.fetch_one(
            f"SELECT conversation_id, created_at, title, chatkit_meta FROM {self._conv} WHERE conversation_id = %s",
            (thread_id,),
        )
        if row is None:
            raise ThreadNotFound(thread_id)
        return self._row_to_thread(row)

    async def save_thread(self, thread: ThreadMetadata, context: RequestContext) -> None:
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
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) AS new "
            "ON DUPLICATE KEY UPDATE title = new.title, chatkit_meta = new.chatkit_meta, "
            "status = IF(agent_conversations.status = 2, 2, new.status)",  # alias `new`: MySQL >= 8.0.19
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
                _to_db(thread.created_at),
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
        await self._db.execute(f"DELETE FROM {self._conv} WHERE conversation_id = %s", (thread_id,))

    # ---- items -----------------------------------------------------------

    async def load_thread_items(
        self, thread_id: str, after: str | None, limit: int, order: str, context: RequestContext
    ) -> Page[ThreadItem]:
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
        payload = json.dumps(item.model_dump(mode="json"), ensure_ascii=False)
        await self._db.execute(
            f"INSERT INTO {self._msg} (message_id, conversation_id, seq, item_type, payload, created_at) "
            f"SELECT %s, %s, COALESCE(MAX(seq), 0) + 1, %s, %s, %s FROM {self._msg} WHERE conversation_id = %s",
            (item.id, thread_id, item.type, payload, _to_db(item.created_at), thread_id),
        )

    async def save_item(self, thread_id: str, item: ThreadItem, context: RequestContext) -> None:
        exists = await self._db.fetch_one(
            f"SELECT 1 AS x FROM {self._msg} WHERE conversation_id = %s AND message_id = %s", (thread_id, item.id)
        )
        if exists is None:
            await self.add_thread_item(thread_id, item, context)
            return
        payload = json.dumps(item.model_dump(mode="json"), ensure_ascii=False)
        await self._db.execute(
            f"UPDATE {self._msg} SET item_type = %s, payload = %s WHERE conversation_id = %s AND message_id = %s",
            (item.type, payload, thread_id, item.id),
        )

    async def load_item(self, thread_id: str, item_id: str, context: RequestContext) -> ThreadItem:
        row = await self._db.fetch_one(
            f"SELECT payload FROM {self._msg} WHERE conversation_id = %s AND message_id = %s", (thread_id, item_id)
        )
        if row is None:
            raise ItemNotFound(item_id)
        return self._row_to_item(row)

    async def delete_thread_item(self, thread_id: str, item_id: str, context: RequestContext) -> None:
        await self._db.execute(
            f"DELETE FROM {self._msg} WHERE conversation_id = %s AND message_id = %s", (thread_id, item_id)
        )

    async def last_activity(self, thread_id: str) -> datetime | None:
        """Fecha (UTC naive) del ultimo mensaje de la conversacion, o de su creacion si no hay mensajes."""
        row = await self._db.fetch_one(
            f"SELECT COALESCE(MAX(m.created_at), c.created_at) AS last FROM {self._conv} c "
            f"LEFT JOIN {self._msg} m ON m.conversation_id = c.conversation_id "
            "WHERE c.conversation_id = %s GROUP BY c.conversation_id",
            (thread_id,),
        )
        return row["last"] if row and row["last"] else None

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
