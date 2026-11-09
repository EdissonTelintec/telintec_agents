# -*- coding: utf-8 -*-
"""Respuesta HTTP de una peticion del protocolo de ChatKit, comun a los dos agentes:
stream `text/event-stream` o JSON segun la operacion; 404 con el envelope si el hilo no existe.

En las operaciones con stream ChatKit carga el hilo hasta que se itera el stream, ya con el 200 enviado;
por eso se lee el primer evento antes de responder. Ese evento sale antes de correr el agente
(`thread.created` o el mensaje del usuario ya guardado), asi que no retrasa la respuesta.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi import Response
from fastapi.responses import JSONResponse, StreamingResponse
from chatkit.server import ChatKitServer, StreamingResult

from agents_service.context import RequestContext


def _not_found(error: LookupError) -> JSONResponse:
    return JSONResponse({"data": None, "msg": "Conversación no encontrada", "error": str(error)}, status_code=404)


async def _prepend(first: bytes | None, rest: AsyncIterator[bytes]) -> AsyncIterator[bytes]:
    if first is not None:
        yield first
    async for chunk in rest:
        yield chunk


async def chatkit_response(server: ChatKitServer[RequestContext], body: bytes, context: RequestContext) -> Response:
    try:
        result = await server.process(body, context)
    except LookupError as e:  # conversacion o mensaje inexistente (p. ej. borrado por la retencion)
        return _not_found(e)
    if isinstance(result, StreamingResult):
        stream = aiter(result)
        try:
            first: bytes | None = await anext(stream)
        except LookupError as e:
            return _not_found(e)
        except StopAsyncIteration:
            first = None
        return StreamingResponse(
            _prepend(first, stream),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )
    return Response(content=result.json, media_type="application/json")
