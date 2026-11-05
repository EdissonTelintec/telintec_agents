# -*- coding: utf-8 -*-
"""`GET /agents/health` -> `OK` (texto). Healthcheck de nginx/systemd; no toca la BD."""

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

router = APIRouter()


@router.get("/health", response_class=PlainTextResponse)
async def health() -> str:
    return "OK"
