# -*- coding: utf-8 -*-
"""Servidor simulado para el front (`agents_service/mock.py`): sin BD ni OpenAI, corre siempre.

- ventas: stream palabra por palabra, escenarios por palabra clave, textos fijos en un solo evento,
  historial del hilo, sin lista de conversaciones para el visitante;
- asistente: mismo 401 que el servicio, token sin verificar firma, eco de `X-Page-Context` y del token,
  cita de la guia, lista de conversaciones solo del usuario;
- CORS: localhost pasa, otro origen no.
"""

from __future__ import annotations

import json
import time

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi.testclient import TestClient

from agents_service.agents import assistant as assistant_texts
from agents_service.agents import sales as sales_texts
from agents_service.mock import create_mock_app, load_settings_for_mock

SALES = "/agents/sales/chatkit"
ASSISTANT = "/agents/assistant/chatkit"
LIST = {"type": "threads.list", "params": {"limit": 10, "order": "desc", "after": None}}


def _input(text: str) -> dict:
    return {"content": [{"type": "input_text", "text": text}], "attachments": [], "quoted_text": None, "inference_options": {}}


def _create(text: str) -> dict:
    return {"type": "threads.create", "params": {"input": _input(text)}}


def _follow(thread_id: str, text: str) -> dict:
    return {"type": "threads.add_user_message", "params": {"thread_id": thread_id, "input": _input(text)}}


def _events(text: str) -> list[dict]:
    return [json.loads(line[5:].strip()) for line in text.splitlines() if line.startswith("data:")]


def _done_texts(events: list[dict]) -> list[str]:
    return [
        "".join(c["text"] for c in e["item"]["content"])
        for e in events
        if e["type"] == "thread.item.done" and e["item"]["type"] == "assistant_message"
    ]


def _deltas(events: list[dict]) -> str:
    return "".join(
        e["update"]["delta"]
        for e in events
        if e["type"] == "thread.item.updated" and e["update"]["type"] == "assistant_message.content_part.text_delta"
    )


def _thread_id(events: list[dict]) -> str:
    return next(e["thread"]["id"] for e in events if e["type"] == "thread.created")


def _token(claims: dict | None = None, lifetime: int = 3600, alg: str = "ES256") -> str:
    """Firmado con una llave cualquiera: el simulado no verifica la firma."""
    now = int(time.time())
    payload = {"user": "front", "emp_id": 7, "name": "Front Dev", "permissions": {"0": "App.Department.Basic"}, "iat": now, "exp": now + lifetime}
    payload.update(claims or {})
    key = ec.generate_private_key(ec.SECP256R1()) if alg == "ES256" else "secreto-hs256-de-prueba-con-32-bytes!"
    return jwt.encode(payload, key, algorithm=alg, headers={"kid": "lambda"})


@pytest.fixture
def client():
    with TestClient(create_mock_app(delay=0)) as c:
        yield c


def test_health(client):
    r = client.get("/agents/health")
    assert r.status_code == 200 and r.text == "OK"


def test_sales_streams_and_keeps_history(client):
    r = client.post(SALES, json=_create("hola"))
    assert r.status_code == 200 and r.headers["content-type"].startswith("text/event-stream")
    events = _events(r.text)
    [text] = _done_texts(events)
    assert "Robotín" in text and "«hola»" in text
    assert _deltas(events) == text  # llego palabra por palabra

    thread_id = _thread_id(events)
    events = _events(client.post(SALES, json=_follow(thread_id, "busco un producto")).text)
    [text] = _done_texts(events)
    assert "![CS-DB2KIT](https://ftp3.syscom.mx/" in text and "precios son de lista" in text

    items = client.post(SALES, json={"type": "items.list", "params": {"thread_id": thread_id, "limit": 20, "order": "asc", "after": None}}).json()
    assert [i["type"] for i in items["data"]] == ["user_message", "assistant_message"] * 2
    thread = client.post(SALES, json={"type": "threads.get_by_id", "params": {"thread_id": thread_id}}).json()
    assert thread["allowed_image_domains"] == ["ftp3.syscom.mx"]
    assert client.post(SALES, json=LIST).json()["data"] == []  # el visitante no tiene lista


@pytest.mark.parametrize(
    ("message", "kind"),
    [("llegué al tope", "limit"), ("algo fuera de tema", "off_topic"), ("provoca un error", "error")],
)
def test_sales_fixed_texts_in_one_event(client, message, kind):
    events = _events(client.post(SALES, json=_create(message)).text)
    assert _done_texts(events) == [sales_texts.fixed_text(kind, load_settings_for_mock())]
    assert _deltas(events) == ""


def test_sales_quote_is_simulated(client):
    [text] = _done_texts(_events(client.post(SALES, json=_create("quiero una cotización")).text))
    assert "SIM-0001" in text and "no se guardó nada" in text


def test_unknown_thread_is_404(client):
    # routers/_chatkit.py es el del servicio: 404 tambien en las operaciones con stream (antes era un 200 cortado)
    for body in (
        {"type": "threads.get_by_id", "params": {"thread_id": "thr_noexiste"}},
        _follow("thr_noexiste", "hola"),
    ):
        r = client.post(SALES, json=body)
        assert r.status_code == 404 and r.json()["msg"] == "Conversación no encontrada"
        assert r.json()["error"] == "thr_noexiste"


def test_assistant_auth_like_the_service(client):
    r = client.post(ASSISTANT, json=_create("hola"))
    assert r.status_code == 401
    assert r.json() == {"data": None, "msg": "No autorizado. Token invalido", "error": "falta el encabezado Authorization"}
    assert client.post(ASSISTANT, json=_create("hola"), headers={"Authorization": "Bearer " + _token()}).status_code == 401
    r = client.post(ASSISTANT, json=_create("hola"), headers={"Authorization": _token(alg="HS256")})
    assert r.status_code == 401 and "ES256" in r.json()["error"]
    assert client.post(ASSISTANT, json=_create("hola"), headers={"Authorization": _token(lifetime=-120)}).status_code == 401
    assert client.post(ASSISTANT, json=_create("hola"), headers={"Authorization": _token(lifetime=25 * 3600)}).status_code == 401

    me = client.get("/agents/assistant/me", headers={"Authorization": _token()}).json()
    assert me["data"]["emp_id"] == 7 and me["data"]["permissions"] == ["App.Department.Basic"]


def test_assistant_echoes_page_and_user_and_lists_only_own_threads(client):
    headers = {"Authorization": _token(), "X-Page-Context": "/dashboard/almacen/entradas?x=1"}
    events = _events(client.post(ASSISTANT, json=_create("dame la guía"), headers=headers).text)
    [text] = _done_texts(events)
    assert "Front Dev" in text and "emp_id 7" in text and "`almacen.md`" in text and "App.Department.Basic" in text
    done = next(e for e in events if e["type"] == "thread.item.done" and e["item"]["type"] == "assistant_message")
    [annotation] = done["item"]["content"][0]["annotations"]
    assert annotation["source"]["type"] == "file" and annotation["source"]["filename"] == "almacen.md"

    own = client.post(ASSISTANT, json=LIST, headers=headers).json()["data"]
    assert [t["id"] for t in own] == [_thread_id(events)]
    other = {"Authorization": _token({"emp_id": 8, "user": "otro"})}
    assert client.post(ASSISTANT, json=LIST, headers=other).json()["data"] == []
    assert _done_texts(_events(client.post(ASSISTANT, json=_create("tope"), headers=other).text)) == [
        assistant_texts.LIMIT_TEXT
    ]


def test_cors_accepts_localhost_only(client):
    preflight = {"Access-Control-Request-Method": "POST", "Access-Control-Request-Headers": "authorization,content-type,x-page-context"}
    r = client.options(ASSISTANT, headers={"Origin": "http://localhost:3000", **preflight})
    assert r.status_code == 200 and r.headers["access-control-allow-origin"] == "http://localhost:3000"
    assert client.options(SALES, headers={"Origin": "https://otro.example", **preflight}).status_code == 400
