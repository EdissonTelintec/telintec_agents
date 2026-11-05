# -*- coding: utf-8 -*-
"""Solicitudes de cotizacion, topes y retencion contra la BD de dev (se salta sin BD)."""

from __future__ import annotations

import dataclasses
from datetime import datetime, timedelta, timezone

import pytest
from chatkit.types import ThreadMetadata

from agents_service.config import load_settings
from agents_service.context import AGENT_SALES, RequestContext, hash_ip
from agents_service.db import Database
from agents_service.limits import REASON_IP, REASON_MESSAGES, REASON_TOKENS, Limits
from agents_service.quotes import InvalidQuoteRequest, QuoteProduct, QuoteRequest, get_quote_request, mark_notified, register_quote_request
from agents_service.retention import purge_conversations
from agents_service.store import MySQLStore


def test_validate_requires_name_and_contact():
    with pytest.raises(InvalidQuoteRequest):
        QuoteRequest(conversation_id="t", name="  ").validate()
    with pytest.raises(InvalidQuoteRequest):
        QuoteRequest(conversation_id="t", name="Ana", phone="123", email="no-es-correo").validate()
    ok = QuoteRequest(conversation_id="t", name=" Ana ", phone="(81) 1234-5678", products=[QuoteProduct(name=" x ", quantity=0)])
    ok.validate()
    assert ok.name == "Ana" and ok.phone == "8112345678" and ok.email is None and ok.products[0].quantity == 1


@pytest.fixture
async def env():
    try:
        settings = load_settings()
    except RuntimeError as e:
        pytest.skip(f"sin .env utilizable: {e}")
    if settings.environment != "dev":
        pytest.skip("solo contra dev")
    db = Database(settings)
    try:
        await db.fetch_one("SELECT 1 AS x")
    except Exception as e:  # noqa: BLE001
        await db.close()
        pytest.skip(f"BD de dev no disponible: {e}")
    try:
        yield settings, db
    finally:
        await db.close()


async def _new_thread(store: MySQLStore, ctx: RequestContext) -> ThreadMetadata:
    thread = ThreadMetadata(id=store.generate_thread_id(ctx), created_at=datetime.now(timezone.utc))
    await store.save_thread(thread, ctx)
    return thread


async def test_quote_request_roundtrip(env):
    settings, db = env
    store = MySQLStore(db, settings.db_agents)
    ctx = RequestContext(agent=AGENT_SALES, user_ref="pytest-quotes")
    thread = await _new_thread(store, ctx)
    now = datetime(2026, 11, 5, 12, 0, 0)
    try:
        req = QuoteRequest(conversation_id=thread.id, name="Ana Pérez", email="ANA@EJEMPLO.MX",
                           products=[QuoteProduct(name="Switch", quantity=2, product_id=1)])
        request_id = await register_quote_request(db, req, now, settings.db_agents)
        row = await get_quote_request(db, request_id, settings.db_agents)
        assert row and row["name"] == "Ana Pérez" and row["email"] == "ana@ejemplo.mx" and row["status"] == 0
        assert row["notified_at"] is None and '"product_id": 1' in row["products"]
        await mark_notified(db, request_id, now, settings.db_agents)
        row = await get_quote_request(db, request_id, settings.db_agents)
        assert row and row["notified_at"] == now
        # la conversacion con solicitud no se purga aunque sea vieja
        assert await purge_conversations(db, now + timedelta(days=400), 90, settings.db_agents) >= 0
        assert await store.load_thread(thread.id, ctx)
    finally:
        await db.execute(f"DELETE FROM {settings.db_agents}.agent_quote_requests WHERE conversation_id = %s", (thread.id,))
        await store.delete_thread(thread.id, ctx)


async def test_limits(env):
    settings, db = env
    tiny = dataclasses.replace(settings, limit_messages_per_conversation=1, limit_conversations_per_ip_day=1, limit_tokens_per_day_sales=10**12)
    limits = Limits(db, tiny)
    store = MySQLStore(db, tiny.db_agents)
    ip = hash_ip("203.0.113.9")
    ctx = RequestContext(agent=AGENT_SALES, ip_hash=ip, user_ref="pytest-limits")
    t1 = await _new_thread(store, ctx)
    t2 = None
    try:
        assert (await limits.check(ctx, t1.id, is_new_conversation=True)).ok  # 1 conversacion hoy: dentro del tope
        t2 = await _new_thread(store, ctx)
        chk = await limits.check(ctx, t2.id, is_new_conversation=True)
        assert not chk.ok and chk.reason == REASON_IP
        assert (await limits.check(ctx, t1.id, is_new_conversation=False)).ok  # 0 mensajes
        from tests.test_store import _user  # reutiliza el helper
        await store.add_thread_item(t1.id, _user(t1.id, "uno", 91), ctx)
        await store.add_thread_item(t1.id, _user(t1.id, "dos", 92), ctx)
        chk = await limits.check(ctx, t1.id, is_new_conversation=False)
        assert not chk.ok and chk.reason == REASON_MESSAGES
        before = await limits.tokens_today(AGENT_SALES)
        await limits.record_usage(AGENT_SALES, t1.id, 120, 30)
        assert await limits.tokens_today(AGENT_SALES) == before + 150
        conv = await db.fetch_one(f"SELECT tokens_in, tokens_out FROM {tiny.db_agents}.agent_conversations WHERE conversation_id = %s", (t1.id,))
        assert conv and conv["tokens_in"] == 120 and conv["tokens_out"] == 30
        zero = dataclasses.replace(tiny, limit_tokens_per_day_sales=1)
        chk = await Limits(db, zero).check(ctx, t1.id, is_new_conversation=False)
        assert not chk.ok and chk.reason == REASON_TOKENS
    finally:
        # deja el consumo del dia como estaba
        await db.execute(f"UPDATE {tiny.db_agents}.agent_usage_daily SET turns = turns - 1, tokens_in = tokens_in - 120, tokens_out = tokens_out - 30 WHERE day = %s AND agent = %s", (limits.now().date(), AGENT_SALES))
        await store.delete_thread(t1.id, ctx)
        if t2:
            await store.delete_thread(t2.id, ctx)


async def test_purge_old_conversation(env):
    settings, db = env
    store = MySQLStore(db, settings.db_agents)
    ctx = RequestContext(agent=AGENT_SALES, user_ref="pytest-purge")
    old = ThreadMetadata(id=store.generate_thread_id(ctx), created_at=datetime(2025, 1, 1, tzinfo=timezone.utc))
    await store.save_thread(old, ctx)
    try:
        deleted = await purge_conversations(db, datetime(2026, 11, 5), 90, settings.db_agents)
        assert deleted >= 1
        with pytest.raises(LookupError):
            await store.load_thread(old.id, ctx)
    finally:
        await store.delete_thread(old.id, ctx)
