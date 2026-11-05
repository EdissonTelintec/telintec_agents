# -*- coding: utf-8 -*-
"""`POST /agents/sales/chatkit`: el widget de ChatKit del sitio publico (sin token).

El cuerpo es una peticion del protocolo de ChatKit; la respuesta es un stream de eventos
(`text/event-stream`) o un JSON, segun la operacion. Sin servidor configurado (falta la llave de
OpenAI) responde 503 con el envelope del API.
"""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Request, Response
from fastapi.responses import JSONResponse

from agents_service.context import AGENT_SALES, CHANNEL_WEB, RequestContext, hash_ip
from agents_service.routers._chatkit import chatkit_response

router = APIRouter()


def client_ip(request: Request, trust_proxy: bool) -> str | None:
    if trust_proxy:
        forwarded = request.headers.get("x-forwarded-for", "")
        if forwarded:
            return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


@router.post("/chatkit")
async def chatkit(request: Request) -> Response:
    server = getattr(request.app.state, "sales_server", None)
    if server is None:
        return JSONResponse({"data": None, "msg": "Agente de ventas no configurado", "error": "OPENAI_API_KEY_SALES"}, status_code=503)
    settings = request.app.state.settings
    context = RequestContext(agent=AGENT_SALES, channel=CHANNEL_WEB, ip_hash=hash_ip(client_ip(request, settings.trust_proxy)))
    return await chatkit_response(server, await request.body(), context)


@router.post("/telegram")
async def telegram_webhook(request: Request, background: BackgroundTasks) -> Response:
    """Webhook de Telegram (F2). Verifica el secreto del encabezado y procesa el update en segundo plano:
    Telegram solo espera un 200 rapido."""
    channel = getattr(request.app.state, "telegram_channel", None)
    settings = request.app.state.settings
    if channel is None or not settings.telegram_webhook_secret:
        return JSONResponse({"data": None, "msg": "Canal Telegram no configurado", "error": "TELEGRAM_TOKEN"}, status_code=503)
    if request.headers.get("x-telegram-bot-api-secret-token") != settings.telegram_webhook_secret:
        return JSONResponse({"data": None, "msg": "No autorizado", "error": "secret_token"}, status_code=403)
    try:
        update = await request.json()
    except ValueError:
        return JSONResponse({"data": None, "msg": "Cuerpo inválido", "error": "json"}, status_code=400)
    background.add_task(channel.handle_update, update)
    return JSONResponse({"ok": True})
