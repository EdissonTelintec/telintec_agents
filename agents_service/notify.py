# -*- coding: utf-8 -*-
"""Aviso a ventas de una solicitud de cotizacion.

Canal principal (decision del usuario, 2026-11-05): el **sistema interno de notificaciones** del API
(`sql_telintec.notifications_gui`, el mismo que lee `GET /misc/notifications/all/<status>` de la webapp):
se inserta una fila con el `body` de siempre y `app` = claves de permiso que la ven
(`QUOTE_NOTIFY_APPS`, por defecto `administracion` y `adminpreventa`). Requiere `INSERT` en esa tabla
para `agents_svc` (scripts_db_handle/agentes_grants_v3.sql del API).

Canal secundario, para despues: correo por SES con la identidad del API (`SES_SENDER`, `SES_REGION`);
solo se intenta si esta configurado. Ningun canal lanza: la solicitud ya quedo guardada en la BD.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime

from agents_service.config import Settings
from agents_service.db import Database
from agents_service.quotes import QuoteRequest

log = logging.getLogger("agents.notify")

TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"


def _products_line(req: QuoteRequest) -> str:
    if not req.products:
        return "sin productos indicados"
    return "; ".join(f"{p.quantity} x {p.name}" + (f" (id {p.product_id})" if p.product_id else "") for p in req.products)


def build_notification_body(req: QuoteRequest, now: datetime, apps: tuple[str, ...]) -> dict:
    """Cuerpo con la forma que usa el API (`NotificationForm`): id, title, msg, status, sender_id,
    timestamp, receiver_id, app, extra_emps."""
    contact = " · ".join(x for x in (req.phone, req.email, req.company) if x)
    msg = f"{req.name} ({contact}) pide cotizar: {_products_line(req)}."
    if req.message:
        msg += f" Mensaje: {req.message}"
    msg += f" Conversación {req.conversation_id}."
    return {
        "id": 0,
        "app": list(apps),
        "title": f"Solicitud de cotización #{req.request_id} (Robotín)",
        "msg": msg[:1000],
        "status": 0,
        "sender_id": 0,
        "timestamp": now.strftime(TIMESTAMP_FORMAT),
        "receiver_id": 0,
        "extra_emps": [],
    }


async def create_internal_notification(db: Database, settings: Settings, req: QuoteRequest, now: datetime) -> int | None:
    """Inserta la notificacion interna; devuelve su id o None si fallo (queda en el log)."""
    body = build_notification_body(req, now, settings.quote_notify_apps)
    try:
        _, notification_id = await db.execute(
            f"INSERT INTO {settings.db_catalog}.notifications_gui (body, timestamp) VALUES (%s, %s)",
            (json.dumps(body, ensure_ascii=False), now.strftime(TIMESTAMP_FORMAT)),
        )
        return notification_id or None
    except Exception as e:  # noqa: BLE001 - el aviso no debe tirar la conversacion
        log.error("notificacion interna de la solicitud #%s fallo: %s", req.request_id, e)
        return None


def build_email(req: QuoteRequest, whatsapp_url: str) -> tuple[str, str]:
    """(asunto, cuerpo en texto) del aviso por correo (canal secundario)."""
    lines = [
        "Robotin levanto una solicitud de cotizacion desde el chat.",
        "",
        f"Folio: {req.request_id}",
        f"Nombre: {req.name}",
        f"Telefono: {req.phone or '-'}",
        f"Correo: {req.email or '-'}",
        f"Empresa: {req.company or '-'}",
        "",
        "Productos o servicios de interes:",
    ]
    if req.products:
        for p in req.products:
            ref = f" (id {p.product_id})" if p.product_id else " (fuera de catalogo)"
            lines.append(f"  - {p.quantity} x {p.name}{ref}")
    else:
        lines.append("  - (no indico productos)")
    if req.message:
        lines += ["", "Mensaje del visitante:", req.message]
    lines += ["", f"Conversacion: {req.conversation_id}", f"WhatsApp del sitio: {whatsapp_url}"]
    subject = f"[Robotin] Solicitud de cotizacion #{req.request_id}: {req.name}"
    return subject, "\n".join(lines)


def ses_configured(settings: Settings) -> bool:
    return bool(settings.ses_sender and settings.ses_region and settings.sales_emails)


def send_quote_request_email(settings: Settings, req: QuoteRequest) -> bool:
    """True si SES acepto el correo. Nunca lanza: el error va al log. No hace nada si SES no esta configurado."""
    if not ses_configured(settings):
        return False
    subject, body = build_email(req, settings.sales_whatsapp_url)
    try:
        import boto3  # import tardio: solo cuando hay que mandar

        client = boto3.client("ses", region_name=settings.ses_region)
        client.send_email(
            Source=settings.ses_sender,
            Destination={"ToAddresses": list(settings.sales_emails)},
            Message={
                "Subject": {"Data": subject, "Charset": "UTF-8"},
                "Body": {"Text": {"Data": body, "Charset": "UTF-8"}},
            },
            ReplyToAddresses=[req.email] if req.email else [],
        )
        return True
    except Exception as e:  # noqa: BLE001
        log.error("SES fallo para la solicitud #%s: %s", req.request_id, e)
        return False
