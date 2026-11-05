# -*- coding: utf-8 -*-
"""Solicitudes de cotizacion (`agent_quote_requests`): lo que levanta el agente virtual de ventas.

Estados: 0 nueva, 1 contactada, 2 cotizada, 3 descartada (numericos; el front mapea etiquetas).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from agents_service.db import Database

STATUS_NEW = 0

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class InvalidQuoteRequest(ValueError):
    pass


@dataclass
class QuoteProduct:
    name: str
    quantity: int = 1
    product_id: int | None = None  # None = fuera de catalogo


@dataclass
class QuoteRequest:
    conversation_id: str
    name: str
    phone: str | None = None
    email: str | None = None
    company: str | None = None
    message: str | None = None
    products: list[QuoteProduct] = field(default_factory=list)
    request_id: int | None = None

    def validate(self) -> None:
        if not self.name or not self.name.strip():
            raise InvalidQuoteRequest("falta el nombre")
        phone = re.sub(r"[^\d+]", "", self.phone or "")
        email = (self.email or "").strip().lower()
        if len(phone) < 8 and not _EMAIL_RE.match(email):
            raise InvalidQuoteRequest("hace falta un telefono (al menos 8 digitos) o un correo valido")
        self.phone = phone or None
        self.email = email or None
        self.name = self.name.strip()[:150]
        self.company = (self.company or "").strip()[:150] or None
        self.message = (self.message or "").strip()[:2000] or None
        self.products = [p for p in self.products if p.name and p.name.strip()]
        for p in self.products:
            p.name = p.name.strip()[:250]
            p.quantity = max(1, int(p.quantity or 1))

    def products_json(self) -> str:
        return json.dumps(
            [{"product_id": p.product_id, "name": p.name, "quantity": p.quantity} for p in self.products],
            ensure_ascii=False,
        )


async def register_quote_request(db: Database, req: QuoteRequest, now: datetime, schema: str = "sql_telintec_mod_agents") -> int:
    """Valida y guarda la solicitud; devuelve `request_id`."""
    req.validate()
    _, request_id = await db.execute(
        f"INSERT INTO {schema}.agent_quote_requests "
        "(conversation_id, name, phone, email, company, message, products, status, created_at) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
        (req.conversation_id, req.name, req.phone, req.email, req.company, req.message, req.products_json(), STATUS_NEW, now),
    )
    req.request_id = request_id
    return request_id


async def mark_notified(db: Database, request_id: int, now: datetime, schema: str = "sql_telintec_mod_agents") -> None:
    await db.execute(f"UPDATE {schema}.agent_quote_requests SET notified_at = %s WHERE request_id = %s", (now, request_id))


async def get_quote_request(db: Database, request_id: int, schema: str = "sql_telintec_mod_agents") -> dict[str, Any] | None:
    return await db.fetch_one(f"SELECT * FROM {schema}.agent_quote_requests WHERE request_id = %s", (request_id,))
