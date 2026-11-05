# -*- coding: utf-8 -*-
"""`POST /agents/sales/chatkit`: el widget de ChatKit del sitio publico (sin token).

El cuerpo es una peticion del protocolo de ChatKit; la respuesta es un stream de eventos
(`text/event-stream`) o un JSON, segun la operacion. Sin servidor configurado (falta la llave de
OpenAI) responde 503 con el envelope del API.
"""

from __future__ import annotations

from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse
from chatkit.server import StreamingResult

from agents_service.context import AGENT_SALES, CHANNEL_WEB, RequestContext, hash_ip

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
    body = await request.body()
    try:
        result = await server.process(body, context)
    except LookupError as e:  # conversacion o mensaje inexistente
        return JSONResponse({"data": None, "msg": "Conversación no encontrada", "error": str(e)}, status_code=404)
    if isinstance(result, StreamingResult):
        return StreamingResponse(
            result,
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )
    return Response(content=result.json, media_type="application/json")
