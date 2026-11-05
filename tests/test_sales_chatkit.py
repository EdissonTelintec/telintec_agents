# -*- coding: utf-8 -*-
"""`POST /agents/sales/chatkit` con el protocolo de ChatKit.

- sin llave de OpenAI -> 503;
- con tope de mensajes en 0 -> respuesta fija por el stream sin llamar al modelo (BD de dev);
- RUN_LIVE=1 -> una conversacion real contra OpenAI (cuesta centavos; requiere la llave en el .env).
"""

from __future__ import annotations

import dataclasses
import json
import os

import pytest
from fastapi.testclient import TestClient

from agents_service.config import load_settings
from agents_service.context import AGENT_SALES, RequestContext
from agents_service.main import create_app
from agents_service.store import MySQLStore

CREATE = {
    "type": "threads.create",
    "params": {"input": {"content": [{"type": "input_text", "text": "Hola, busco un switch PoE de 8 puertos"}], "attachments": [], "quoted_text": None, "inference_options": {}}},
}


def _events(text: str) -> list[dict]:
    out = []
    for line in text.splitlines():
        if line.startswith("data:"):
            out.append(json.loads(line[5:].strip()))
    return out


def _assistant_texts(events: list[dict]) -> list[str]:
    texts = []
    for e in events:
        item = e.get("item") or {}
        if e.get("type") == "thread.item.done" and item.get("type") == "assistant_message":
            texts.append("".join(c.get("text", "") for c in item.get("content", [])))
    return texts


def test_without_key_returns_503(settings):
    with TestClient(create_app(settings)) as client:
        r = client.post("/agents/sales/chatkit", json=CREATE)
        assert r.status_code == 503 and r.json()["error"] == "OPENAI_API_KEY_SALES"


@pytest.fixture
def dev_settings():
    try:
        s = load_settings()
    except RuntimeError as e:
        pytest.skip(f"sin .env utilizable: {e}")
    if s.environment != "dev":
        pytest.skip("solo contra dev")
    return s


def test_limit_path_streams_fixed_message(dev_settings):
    s = dataclasses.replace(dev_settings, limit_messages_per_conversation=0, openai_api_key_sales=dev_settings.openai_api_key_sales or "sk-prueba")
    app = create_app(s)
    with TestClient(app) as client:
        r = client.post("/agents/sales/chatkit", json=CREATE, headers={"X-Forwarded-For": "198.51.100.7"})
        assert r.status_code == 200 and r.headers["content-type"].startswith("text/event-stream")
        events = _events(r.text)
        created = next(e for e in events if e["type"] == "thread.created")
        thread_id = created["thread"]["id"]
        texts = _assistant_texts(events)
        assert texts and s.sales_whatsapp_url in texts[-1]
    # persistido: la conversacion, el mensaje del usuario y la respuesta fija
    import asyncio

    async def check_and_clean():
        store: MySQLStore = app.state.store
        ctx = RequestContext(agent=AGENT_SALES)
        page = await store.load_thread_items(thread_id, after=None, limit=10, order="asc", context=ctx)
        types = [i.type for i in page.data]
        assert types == ["user_message", "assistant_message"], types
        await store.delete_thread(thread_id, ctx)
        await app.state.db.close()

    asyncio.run(check_and_clean())


@pytest.mark.skipif(os.environ.get("RUN_LIVE") != "1", reason="RUN_LIVE=1 para hablar con OpenAI")
def test_live_conversation(dev_settings):
    if not dev_settings.openai_api_key_sales:
        pytest.skip("sin OPENAI_API_KEY_SALES")
    app = create_app(dev_settings)
    with TestClient(app) as client:
        r = client.post("/agents/sales/chatkit", json=CREATE)
        assert r.status_code == 200, r.text
        events = _events(r.text)
        thread_id = next(e for e in events if e["type"] == "thread.created")["thread"]["id"]
        texts = _assistant_texts(events)
        print("\n--- Robotín ---\n" + "\n".join(texts))
        assert texts and any("switch" in t.lower() or "poe" in t.lower() for t in texts)
        # segundo turno: fuera de tema -> texto fijo del guardrail
        follow = {"type": "threads.add_user_message", "params": {"thread_id": thread_id, "input": {"content": [{"type": "input_text", "text": "Hazme la tarea de historia sobre la revolución francesa"}], "attachments": [], "quoted_text": None, "inference_options": {}}}}
        r2 = client.post("/agents/sales/chatkit", json=follow)
        assert r2.status_code == 200, r2.text
        texts2 = _assistant_texts(_events(r2.text))
        print("\n--- Robotín (fuera de tema) ---\n" + "\n".join(texts2))
        assert texts2
    import asyncio

    async def clean():
        store: MySQLStore = app.state.store
        ctx = RequestContext(agent=AGENT_SALES)
        conv = await app.state.db.fetch_one(f"SELECT tokens_in, tokens_out FROM {dev_settings.db_agents}.agent_conversations WHERE conversation_id = %s", (thread_id,))
        print("tokens:", conv)
        assert conv and conv["tokens_in"] > 0
        await store.delete_thread(thread_id, ctx)
        await app.state.db.close()

    asyncio.run(clean())
