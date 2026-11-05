# -*- coding: utf-8 -*-
"""Respuesta HTTP de una peticion del protocolo de ChatKit, comun a los dos agentes:
stream `text/event-stream` o JSON segun la operacion; 404 con el envelope si el hilo no existe."""

from __future__ import annotations

from fastapi import Response
from fastapi.responses import JSONResponse, StreamingResponse
from chatkit.server import ChatKitServer, StreamingResult

from agents_service.context import RequestContext


async def chatkit_response(server: ChatKitServer[RequestContext], body: bytes, context: RequestContext) -> Response:
    try:
        result = await server.process(body, context)
    except LookupError as e:  # conversacion o mensaje inexistente (p. ej. borrado por la retencion)
        return JSONResponse({"data": None, "msg": "Conversación no encontrada", "error": str(e)}, status_code=404)
    if isinstance(result, StreamingResult):
        return StreamingResponse(
            result,
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )
    return Response(content=result.json, media_type="application/json")
