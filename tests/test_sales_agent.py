# -*- coding: utf-8 -*-
"""Agente de ventas sin red: prompt, tools, guardrail helper, textos fijos y correo."""

from __future__ import annotations

import dataclasses

from agents_service.agents.sales import (
    AGENT_NAME,
    MAX_PRODUCTS_PER_ANSWER,
    _last_user_text,
    build_instructions,
    build_sales_agent,
    fixed_text,
    load_knowledge,
)
from agents_service.db import Database
from agents_service.notify import build_email, send_quote_request_email, ses_configured
from agents_service.quotes import QuoteProduct, QuoteRequest


def test_instructions_include_rules_services_and_contact(settings):
    text = build_instructions(settings, services_md="### Servicio de prueba\n- algo")
    assert AGENT_NAME in text and str(MAX_PRODUCTS_PER_ANSWER) in text
    assert "MXN" in text and "IVA" in text and "precio de lista" in text
    assert "Servicio de prueba" in text
    assert settings.sales_whatsapp_url in text and "+52 81 1167 5189" in text
    assert "registrar_solicitud" in text and "buscar_productos" in text


def test_knowledge_file_present():
    assert "Redes e infraestructura" in load_knowledge()


def test_build_agent_tools_and_guardrail(settings):
    s = dataclasses.replace(settings, openai_api_key_sales="sk-prueba", limit_output_tokens=123)
    agent = build_sales_agent(s, Database(s))
    assert agent.name == AGENT_NAME
    assert {t.name for t in agent.tools} == {"buscar_productos", "detalle_producto", "registrar_solicitud"}
    assert len(agent.input_guardrails) == 1
    assert agent.model_settings.max_tokens == 123
    from agents import FunctionTool

    tool = next(t for t in agent.tools if isinstance(t, FunctionTool) and t.name == "registrar_solicitud")
    assert "productos" in tool.params_json_schema["properties"] and "nombre" in tool.params_json_schema["properties"]


def test_last_user_text():
    assert _last_user_text("hola") == "hola"
    items = [
        {"role": "user", "content": "primero"},
        {"role": "assistant", "content": [{"type": "output_text", "text": "respuesta"}]},
        {"role": "user", "content": [{"type": "input_text", "text": "último"}]},
    ]
    assert _last_user_text(items) == "último"
    assert _last_user_text([]) == ""


def test_fixed_texts(settings):
    s = dataclasses.replace(settings, sales_emails=("ventas@telintec.com.mx",))
    assert s.sales_whatsapp_url in fixed_text("limit", s) and "ventas@telintec.com.mx" in fixed_text("limit", s)
    assert "Robotín" in fixed_text("off_topic", s)
    assert s.sales_whatsapp_url in fixed_text("error", s)


def test_build_notification_body():
    from datetime import datetime

    from agents_service.notify import build_notification_body

    req = QuoteRequest(conversation_id="thr_x", name="Ana Pérez", phone="8111111111", company="ACME",
                       products=[QuoteProduct(name="Switch PoE", quantity=2, product_id=5)], request_id=9)
    body = build_notification_body(req, datetime(2026, 11, 5, 15, 30, 0), ("administracion", "adminpreventa"))
    assert body["app"] == ["administracion", "adminpreventa"] and body["status"] == 0 and body["sender_id"] == 0
    assert body["title"] == "Solicitud de cotización #9 (Robotín)"
    assert "Ana Pérez (8111111111 · ACME) pide cotizar: 2 x Switch PoE (id 5)." in body["msg"] and "thr_x" in body["msg"]
    assert body["timestamp"] == "2026-11-05 15:30:00" and body["extra_emps"] == [] and body["receiver_id"] == 0


async def test_create_internal_notification_uses_api_table(settings):
    from datetime import datetime

    from agents_service.notify import create_internal_notification

    class FakeDb:
        def __init__(self):
            self.calls = []

        async def execute(self, sql, args=()):
            self.calls.append((sql, args))
            return 1, 4242

    req = QuoteRequest(conversation_id="thr_x", name="Ana", email="ana@x.mx", request_id=9)
    db = FakeDb()
    nid = await create_internal_notification(db, settings, req, datetime(2026, 11, 5, 15, 30, 0))  # type: ignore[arg-type]
    assert nid == 4242
    sql, args = db.calls[0]
    assert sql.startswith("INSERT INTO sql_telintec.notifications_gui (body, timestamp)")
    assert '"app": ["administracion", "adminpreventa"]' in args[0] and args[1] == "2026-11-05 15:30:00"


def test_build_email():
    req = QuoteRequest(
        conversation_id="thr_x", name="Ana Pérez", phone="8111111111", email=None, company="ACME",
        message="urge", products=[QuoteProduct(name="Switch PoE 8 puertos", quantity=2, product_id=190395), QuoteProduct(name="cámara térmica", quantity=1)],
        request_id=7,
    )
    subject, body = build_email(req, "https://wa.me/x")
    assert "#7" in subject and "Ana Pérez" in subject
    assert "2 x Switch PoE 8 puertos (id 190395)" in body and "cámara térmica (fuera de catalogo)" in body
    assert "ACME" in body and "urge" in body and "thr_x" in body


def test_ses_off_by_default(settings):
    assert not ses_configured(settings)
    assert send_quote_request_email(settings, QuoteRequest(conversation_id="t", name="Ana", request_id=1)) is False
