# -*- coding: utf-8 -*-
"""Store sobre la BD de dev del .env real. Se salta si no hay .env, si apunta a prod o si la BD no responde."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest
from chatkit.types import (
    AssistantMessageContent,
    AssistantMessageItem,
    ClosedStatus,
    InferenceOptions,
    ThreadMetadata,
    UserMessageItem,
    UserMessageTextContent,
)

from agents_service.config import load_settings
from agents_service.context import AGENT_SALES, RequestContext, hash_ip
from agents_service.db import Database
from agents_service.store import DEFAULT_TIMEZONE, ItemNotFound, MySQLStore, ThreadNotFound


@pytest.fixture
async def store():
    try:
        settings = load_settings()
    except RuntimeError as e:
        pytest.skip(f"sin .env utilizable: {e}")
    if settings.environment != "dev":
        pytest.skip("las pruebas del Store solo corren contra dev")
    db = Database(settings)
    try:
        cols = await db.fetch_all(
            "SELECT COLUMN_NAME FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'agent_conversations'",
            (settings.db_agents,),
        )
    except Exception as e:  # noqa: BLE001 - sin BD no hay prueba
        await db.close()
        pytest.skip(f"BD de dev no disponible: {e}")
    names = {c["COLUMN_NAME"] for c in cols}
    if not {"title", "chatkit_meta"} <= names:
        await db.close()
        pytest.skip("faltan las columnas title/chatkit_meta: correr scripts_db_handle/agentes_schema_v2.sql")
    try:
        yield MySQLStore(db, settings.db_agents)
    finally:
        await db.close()


def _user(thread_id: str, text: str, n: int) -> UserMessageItem:
    return UserMessageItem(
        id=f"msg_pytest_u{n}", thread_id=thread_id, created_at=datetime.now(timezone.utc),
        content=[UserMessageTextContent(text=text)],
        inference_options=InferenceOptions(),
    )


def _assistant(thread_id: str, text: str, n: int) -> AssistantMessageItem:
    return AssistantMessageItem(
        id=f"msg_pytest_a{n}", thread_id=thread_id, created_at=datetime.now(timezone.utc),
        content=[AssistantMessageContent(text=text)],
    )


async def test_thread_and_items_roundtrip(store: MySQLStore):
    ctx = RequestContext(agent=AGENT_SALES, user_ref="pytest", ip_hash=hash_ip("127.0.0.1"))
    thread = ThreadMetadata(id=store.generate_thread_id(ctx), created_at=datetime.now(timezone.utc), title="prueba")
    await store.save_thread(thread, ctx)
    try:
        loaded = await store.load_thread(thread.id, ctx)
        assert loaded.id == thread.id and loaded.title == "prueba" and loaded.status.type == "active"
        assert loaded.created_at.tzinfo is not None
        # en la BD queda hora de Mexico naive (como el resto del esquema), y al leerla no se corre 6 h
        assert abs(loaded.created_at - thread.created_at) < timedelta(seconds=2)
        row = await store._db.fetch_one(f"SELECT created_at FROM {store._conv} WHERE conversation_id = %s", (thread.id,))
        local_now = datetime.now(ZoneInfo(DEFAULT_TIMEZONE)).replace(tzinfo=None)
        assert row and abs(row["created_at"] - local_now) < timedelta(minutes=1)
        # un naive (ChatKit usa datetime.now()) se toma como hora del sistema
        last = await store.last_activity(thread.id)
        assert last is not None and last.tzinfo is not None and abs(datetime.now(timezone.utc) - last) < timedelta(minutes=1)

        await store.add_thread_item(thread.id, _user(thread.id, "hola", 1), ctx)
        await store.add_thread_item(thread.id, _assistant(thread.id, "¡Hola! Soy Robotín", 1), ctx)
        await store.add_thread_item(thread.id, _user(thread.id, "busco una cámara", 2), ctx)
        assert await store.count_items(thread.id) == 3
        assert await store.count_items(thread.id, "user_message") == 2

        page = await store.load_thread_items(thread.id, after=None, limit=2, order="asc", context=ctx)
        assert [i.id for i in page.data] == ["msg_pytest_u1", "msg_pytest_a1"] and page.has_more
        rest = await store.load_thread_items(thread.id, after=page.after, limit=2, order="asc", context=ctx)
        assert [i.id for i in rest.data] == ["msg_pytest_u2"] and not rest.has_more
        newest = await store.load_thread_items(thread.id, after=None, limit=1, order="desc", context=ctx)
        assert newest.data[0].id == "msg_pytest_u2"

        item = await store.load_item(thread.id, "msg_pytest_a1", ctx)
        assert isinstance(item, AssistantMessageItem) and item.content[0].text == "¡Hola! Soy Robotín"
        item.content[0].text = "editado"
        await store.save_item(thread.id, item, ctx)
        edited = await store.load_item(thread.id, "msg_pytest_a1", ctx)
        assert isinstance(edited, AssistantMessageItem) and edited.content[0].text == "editado"
        await store.save_item(thread.id, _user(thread.id, "nuevo por save_item", 3), ctx)
        assert await store.count_items(thread.id) == 4

        await store.delete_thread_item(thread.id, "msg_pytest_u3", ctx)
        with pytest.raises(ItemNotFound):
            await store.load_item(thread.id, "msg_pytest_u3", ctx)

        listed = await store.load_threads(limit=5, after=None, order="desc", context=ctx)
        assert thread.id in [t.id for t in listed.data]
        anon = await store.load_threads(limit=5, after=None, order="desc", context=RequestContext(agent=AGENT_SALES))
        assert anon.data == [] and not anon.has_more

        loaded.title = "cerrada"
        loaded.status = ClosedStatus(reason="fin")
        await store.save_thread(loaded, ctx)
        again = await store.load_thread(thread.id, ctx)
        assert again.title == "cerrada" and again.status.type == "closed"
    finally:
        await store.delete_thread(thread.id, ctx)
    with pytest.raises(ThreadNotFound):
        await store.load_thread(thread.id, ctx)
    assert await store.count_items(thread.id) == 0  # cascade
