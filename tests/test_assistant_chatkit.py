# -*- coding: utf-8 -*-
"""`POST /agents/assistant/chatkit` con el protocolo de ChatKit.

- sin token, con `Bearer`, HS256 -> 401 con el envelope; token valido sin llave de OpenAI -> 503;
- tope de mensajes en 0 contra la BD de dev -> texto fijo por el stream, conversacion con `user_ref`
  y `page_context`, y `threads.list` solo del usuario;
- RUN_LIVE=1 -> una conversacion real contra OpenAI (cuesta centavos; requiere la llave en el .env).
"""

from __future__ import annotations

import asyncio
import dataclasses
import json
import os

import pytest
from fastapi.testclient import TestClient

from agents_service.agents.assistant import ERROR_TEXT, LIMIT_TEXT, OFF_TOPIC_TEXT
from agents_service.config import load_settings
from agents_service.context import AGENT_ASSISTANT, CHANNEL_WEB, RequestContext
from agents_service.main import create_app
from agents_service.store import MySQLStore

URL = "/agents/assistant/chatkit"
LIST = {"type": "threads.list", "params": {"limit": 10, "order": "desc", "after": None}}


def _create(text: str) -> dict:
    return {
        "type": "threads.create",
        "params": {"input": {"content": [{"type": "input_text", "text": text}], "attachments": [], "quoted_text": None, "inference_options": {}}},
    }


def _follow(thread_id: str, text: str) -> dict:
    return {
        "type": "threads.add_user_message",
        "params": {
            "thread_id": thread_id,
            "input": {"content": [{"type": "input_text", "text": text}], "attachments": [], "quoted_text": None, "inference_options": {}},
        },
    }


def _events(text: str) -> list[dict]:
    return [json.loads(line[5:].strip()) for line in text.splitlines() if line.startswith("data:")]


def _assistant_texts(events: list[dict]) -> list[str]:
    texts = []
    for e in events:
        item = e.get("item") or {}
        if e.get("type") == "thread.item.done" and item.get("type") == "assistant_message":
            texts.append("".join(c.get("text", "") for c in item.get("content", [])))
    return texts


def test_auth_then_503_without_key(settings, sign):
    with TestClient(create_app(settings)) as client:
        r = client.post(URL, json=_create("hola"))
        assert r.status_code == 401
        assert r.json() == {"data": None, "msg": "No autorizado. Token invalido", "error": "falta el encabezado Authorization"}
        assert client.post(URL, json=_create("hola"), headers={"Authorization": "Bearer " + sign()}).status_code == 401
        r = client.post(URL, json=_create("hola"), headers={"Authorization": sign(alg="HS256", kid=None)})
        assert r.status_code == 401 and "ES256" in r.json()["error"]
        r = client.post(URL, json=_create("hola"), headers={"Authorization": sign()})
        assert r.status_code == 503 and r.json()["error"] == "OPENAI_API_KEY_ASSISTANT"


@pytest.fixture
def dev_settings(keypair):
    try:
        s = load_settings()
    except RuntimeError as e:
        pytest.skip(f"sin .env utilizable: {e}")
    if s.environment != "dev":
        pytest.skip("solo contra dev")
    keys_dir, _ = keypair
    return dataclasses.replace(s, token_keys_dir=keys_dir, token_kids=("test",))


def test_limit_path_persists_user_conversation(dev_settings, sign):
    s = dataclasses.replace(
        dev_settings,
        limit_messages_per_conversation=0,
        openai_api_key_assistant=dev_settings.openai_api_key_assistant or "sk-prueba",
    )
    app = create_app(s)
    ana = sign({"emp_id": 7001, "name": "Ana Prueba", "permissions": {"0": "App.Department.RRHH"}})
    luis = sign({"emp_id": 7002, "name": "Luis Prueba"})
    with TestClient(app) as client:
        r = client.post(
            URL,
            json=_create("¿cómo doy de alta un empleado?"),
            headers={"Authorization": ana, "X-Page-Context": "/dashboard/rrhh/personal?x=1"},
        )
        assert r.status_code == 200 and r.headers["content-type"].startswith("text/event-stream")
        events = _events(r.text)
        thread_id = next(e for e in events if e["type"] == "thread.created")["thread"]["id"]
        assert _assistant_texts(events)[-1] == LIMIT_TEXT
        mine = client.post(URL, json=LIST, headers={"Authorization": ana})
        assert mine.status_code == 200 and thread_id in [t["id"] for t in mine.json()["data"]]
        others = client.post(URL, json=LIST, headers={"Authorization": luis})
        assert others.status_code == 200 and thread_id not in [t["id"] for t in others.json()["data"]]

    async def check_and_clean():
        conv = await app.state.db.fetch_one(
            f"SELECT agent, channel, user_ref, page_context, ip_hash FROM {s.db_agents}.agent_conversations WHERE conversation_id = %s",
            (thread_id,),
        )
        assert conv == {"agent": AGENT_ASSISTANT, "channel": CHANNEL_WEB, "user_ref": "emp:7001", "page_context": "/dashboard/rrhh/personal", "ip_hash": None}
        store: MySQLStore = app.state.store
        await store.delete_thread(thread_id, RequestContext(agent=AGENT_ASSISTANT))
        await app.state.db.close()

    asyncio.run(check_and_clean())


@pytest.mark.skipif(os.environ.get("RUN_LIVE") != "1", reason="RUN_LIVE=1 para hablar con OpenAI")
def test_live_conversation(dev_settings, sign):
    if not dev_settings.openai_api_key_assistant:
        pytest.skip("sin OPENAI_API_KEY_ASSISTANT")
    app = create_app(dev_settings)
    tok = sign({"emp_id": 7001, "name": "Ana Prueba", "permissions": {"0": "App.Department.SM"}})
    with TestClient(app) as client:
        r = client.post(
            URL,
            json=_create("¿Cómo creo una solicitud de material?"),
            headers={"Authorization": tok, "X-Page-Context": "/dashboard/sm/solicitudes"},
        )
        assert r.status_code == 200, r.text
        events = _events(r.text)
        thread_id = next(e for e in events if e["type"] == "thread.created")["thread"]["id"]
        texts = _assistant_texts(events)
        print("\n--- Asistente ---\n" + "\n".join(texts))
        assert texts and ERROR_TEXT not in texts, "el agente fallo (busca 'fallo el agente' en el log)"
        r2 = client.post(URL, json=_follow(thread_id, "Escríbeme un poema sobre el mar"), headers={"Authorization": tok})
        assert r2.status_code == 200, r2.text
        texts2 = _assistant_texts(_events(r2.text))
        print("\n--- Asistente (fuera de tema) ---\n" + "\n".join(texts2))
        # el guardia deja pasar si el modelo nano falla (403, red); sin la igualdad la prueba no lo nota
        assert texts2 == [OFF_TOPIC_TEXT], "no disparo el guardrail (busca 'guardrail fallo' en el log)"

    async def clean():
        conv = await app.state.db.fetch_one(
            f"SELECT tokens_in, tokens_out FROM {dev_settings.db_agents}.agent_conversations WHERE conversation_id = %s", (thread_id,)
        )
        print("tokens:", conv)
        assert conv and conv["tokens_in"] > 0
        store: MySQLStore = app.state.store
        await store.delete_thread(thread_id, RequestContext(agent=AGENT_ASSISTANT))
        await app.state.db.close()

    asyncio.run(clean())
