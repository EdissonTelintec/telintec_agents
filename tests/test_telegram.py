# -*- coding: utf-8 -*-
"""Canal Telegram sin tocar Telegram ni OpenAI: conversor, parseo, ciclo de conversacion y webhook."""

from __future__ import annotations

import dataclasses
from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from agents_service.channels.telegram import (
    START_TEXT,
    UNSUPPORTED_TEXT,
    TelegramChannel,
    markdown_to_telegram_html,
    parse_message,
    split_message,
)
from agents_service.config import load_settings
from agents_service.context import CHANNEL_TELEGRAM, RequestContext
from agents_service.db import Database
from agents_service.limits import Limits
from agents_service.main import create_app
from agents_service.store import MySQLStore


def test_markdown_to_telegram_html():
    md = "## Opciones\n- **Switch PoE** · hikvision · $264.39 MXN\n  ![DS-3E0520HP-E](https://ftp3.syscom.mx/x.png)\nVer [ficha](https://t.mx/a) <b>no</b> `DS-1`"
    out = markdown_to_telegram_html(md)
    assert "<b>Opciones</b>" in out and "• <b>Switch PoE</b>" in out
    assert '<a href="https://ftp3.syscom.mx/x.png">📷 DS-3E0520HP-E</a>' in out
    assert '<a href="https://t.mx/a">ficha</a>' in out and "&lt;b&gt;no&lt;/b&gt;" in out and "<code>DS-1</code>" in out


def test_split_message():
    text = "\n".join(f"línea {i} " + "x" * 50 for i in range(200))
    parts = split_message(text, limit=1000)
    assert all(len(p) <= 1000 for p in parts) and "".join(p.replace("\n", "") for p in parts).replace("\n", "") == text.replace("\n", "")


def test_parse_message():
    upd = {"update_id": 1, "message": {"chat": {"id": 55}, "from": {"id": 7, "first_name": "Ana", "last_name": "P"}, "text": "hola"}}
    assert parse_message(upd) == (55, 7, "hola", "Ana P")
    assert parse_message({"update_id": 2, "message": {"chat": {"id": 55}, "from": {"id": 7}, "photo": []}}) == (55, 7, None, None)
    assert parse_message({"update_id": 3, "callback_query": {}}) is None


class FakeTelegram:
    def __init__(self):
        self.sent: list[tuple[int, str, str | None]] = []
        self.actions: list[tuple[int, str]] = []

    async def send_message(self, chat_id, text, parse_mode="HTML"):
        self.sent.append((chat_id, text, parse_mode))

    async def send_chat_action(self, chat_id, action="typing"):
        self.actions.append((chat_id, action))


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


async def test_conversation_lifecycle_and_turns(env, monkeypatch):
    settings, db = env
    store = MySQLStore(db, settings.db_agents)
    limits = Limits(db, settings)
    fake = FakeTelegram()
    calls = []

    async def fake_run(agent, agent_input, context=None, max_turns=6):
        calls.append(agent_input)
        usage = SimpleNamespace(input_tokens=100, output_tokens=20)
        return SimpleNamespace(final_output="**Switch PoE** para ti ![f](https://ftp3.syscom.mx/x.png)", context_wrapper=SimpleNamespace(usage=usage))

    import agents_service.turn as turn

    monkeypatch.setattr(turn.Runner, "run", fake_run)
    channel = TelegramChannel(fake, store, limits, settings, agent=object(), fixed_text=lambda k: f"[{k}]", session_hours=24)  # type: ignore[arg-type]
    user_id = 990011
    ctx = channel.context_for(user_id)
    created = []
    try:
        # /start abre conversacion y saluda sin modelo
        assert await channel.handle_update({"update_id": 1, "message": {"chat": {"id": 1}, "from": {"id": user_id}, "text": "/start"}}) == START_TEXT
        t1 = (await store.load_threads(1, None, "desc", ctx)).data[0]
        created.append(t1.id)
        assert fake.sent[-1][2] is None and not calls
        # mensaje normal: corre el agente, guarda user+assistant, responde en HTML
        reply = await channel.handle_update({"update_id": 2, "message": {"chat": {"id": 1}, "from": {"id": user_id}, "text": "busco un switch"}})
        assert reply and "Switch PoE" in reply and len(calls) == 1
        assert fake.actions[-1] == (1, "typing") and "<b>Switch PoE</b>" in fake.sent[-1][1] and "📷" in fake.sent[-1][1]
        assert await store.count_items(t1.id, "user_message") == 1 and await store.count_items(t1.id, "assistant_message") == 1
        conv = await db.fetch_one(f"SELECT channel, user_ref, tokens_in FROM {settings.db_agents}.agent_conversations WHERE conversation_id = %s", (t1.id,))
        assert conv and conv["channel"] == CHANNEL_TELEGRAM and conv["user_ref"] == f"telegram:{user_id}" and conv["tokens_in"] == 100
        # segundo mensaje sigue en la misma conversacion y lleva historial
        await channel.handle_update({"update_id": 3, "message": {"chat": {"id": 1}, "from": {"id": user_id}, "text": "de 8 puertos"}})
        assert (await store.load_threads(1, None, "desc", ctx)).data[0].id == t1.id and len(calls[-1]) >= 3
        # sin texto: aviso fijo
        assert await channel.handle_update({"update_id": 4, "message": {"chat": {"id": 1}, "from": {"id": user_id}, "sticker": {}}}) == UNSUPPORTED_TEXT
        # 24 h sin actividad: conversacion nueva y la vieja cerrada
        await db.execute(f"UPDATE {settings.db_agents}.agent_messages SET created_at = %s WHERE conversation_id = %s", (datetime.utcnow() - timedelta(hours=30), t1.id))
        await db.execute(f"UPDATE {settings.db_agents}.agent_conversations SET created_at = %s WHERE conversation_id = %s", (datetime.utcnow() - timedelta(hours=31), t1.id))
        await channel.handle_update({"update_id": 5, "message": {"chat": {"id": 1}, "from": {"id": user_id}, "text": "sigo aquí"}})
        t2 = (await store.load_threads(1, None, "desc", ctx)).data[0]
        created.append(t2.id)
        assert t2.id != t1.id and (await store.load_thread(t1.id, ctx)).status.type == "closed"
        # tope: 0 mensajes por conversacion -> texto fijo sin modelo
        tiny = dataclasses.replace(settings, limit_messages_per_conversation=0)
        channel2 = TelegramChannel(fake, store, Limits(db, tiny), tiny, agent=object(), fixed_text=lambda k: f"[{k}]", session_hours=24)  # type: ignore[arg-type]
        n = len(calls)
        assert await channel2.handle_update({"update_id": 6, "message": {"chat": {"id": 1}, "from": {"id": user_id}, "text": "otra"}}) == "[limit]"
        assert len(calls) == n
    finally:
        await db.execute(f"UPDATE {settings.db_agents}.agent_usage_daily SET turns = turns - 2, tokens_in = tokens_in - 200, tokens_out = tokens_out - 40 WHERE day = %s AND agent = 0", (limits.now().date(),))
        for tid in created:
            await store.delete_thread(tid, ctx)


def test_webhook_endpoint(settings, monkeypatch):
    s = dataclasses.replace(settings, openai_api_key_sales="sk-prueba", telegram_token="123:abc", telegram_webhook_secret="s3cr3t")
    app = create_app(s)
    seen = []

    async def fake_handle(update):
        seen.append(update)

    app.state.telegram_channel.handle_update = fake_handle  # type: ignore[union-attr]
    with TestClient(app) as client:
        body = {"update_id": 9, "message": {"chat": {"id": 1}, "from": {"id": 2}, "text": "hola"}}
        assert client.post("/agents/sales/telegram", json=body).status_code == 403
        assert client.post("/agents/sales/telegram", json=body, headers={"X-Telegram-Bot-Api-Secret-Token": "malo"}).status_code == 403
        r = client.post("/agents/sales/telegram", json=body, headers={"X-Telegram-Bot-Api-Secret-Token": "s3cr3t"})
        assert r.status_code == 200 and r.json() == {"ok": True}
    assert seen == [body]


def test_webhook_without_token_is_503(settings):
    s = dataclasses.replace(settings, openai_api_key_sales="sk-prueba")
    with TestClient(create_app(s)) as client:
        assert client.post("/agents/sales/telegram", json={}).status_code == 503
