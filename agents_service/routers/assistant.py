# -*- coding: utf-8 -*-
"""Asistente de la webapp.

- `POST /agents/assistant/chatkit`: protocolo de ChatKit; JWT crudo ES256 en `Authorization` (401 con el
  envelope del API si falta o no vale) y la ruta actual de la webapp en `X-Page-Context`. Cada usuario ve
  solo sus conversaciones (`user_ref` = `emp:<emp_id>`). 503 sin `OPENAI_API_KEY_ASSISTANT`.
- `GET /agents/assistant/me`: lo que el servicio lee del JWT, para que el front valide la integracion.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import JSONResponse

from agents_service.auth import Unauthorized, current_user, permission_names
from agents_service.context import AGENT_ASSISTANT, CHANNEL_WEB, RequestContext
from agents_service.knowledge import normalize_route
from agents_service.routers._chatkit import chatkit_response

router = APIRouter()

PAGE_CONTEXT_HEADER = "X-Page-Context"


def user_ref(token: dict) -> str:
    """Identidad estable del usuario para sus conversaciones: `emp:<emp_id>`; `user:<user>` si el token
    no trae emp_id."""
    emp_id = token.get("emp_id")
    if emp_id not in (None, ""):
        return f"emp:{emp_id}"
    user = token.get("user")
    if user:
        return f"user:{user}"
    raise Unauthorized("token sin emp_id ni user")


@router.get("/me")
async def me(token: dict = Depends(current_user)) -> dict:
    return {
        "data": {
            "user": token.get("user"),
            "emp_id": token.get("emp_id"),
            "name": token.get("name"),
            "permissions": permission_names(token),
            "exp": token.get("exp"),
        },
        "msg": "ok",
        "error": None,
    }


@router.post("/chatkit")
async def chatkit(request: Request, token: dict = Depends(current_user)) -> Response:
    server = getattr(request.app.state, "assistant_server", None)
    if server is None:
        return JSONResponse(
            {"data": None, "msg": "Asistente no configurado", "error": "OPENAI_API_KEY_ASSISTANT"}, status_code=503
        )
    context = RequestContext(
        agent=AGENT_ASSISTANT,
        channel=CHANNEL_WEB,
        user_ref=user_ref(token),
        page_context=normalize_route(request.headers.get(PAGE_CONTEXT_HEADER)),
        token_data=token,
    )
    return await chatkit_response(server, await request.body(), context)
