# -*- coding: utf-8 -*-
"""Asistente de la webapp (F3 trae el endpoint de ChatKit). En F0 solo `GET /agents/assistant/me`:
devuelve lo que el servicio lee del JWT, para que el front valide la integracion del token."""

from fastapi import APIRouter, Depends

from agents_service.auth import current_user, permission_names

router = APIRouter()


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
