# -*- coding: utf-8 -*-
"""App FastAPI del servicio. `uvicorn agents_service.main:app` en prod; `create_app` en pruebas."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from agents_service.auth import UNAUTHORIZED_MSG, TokenVerifier, Unauthorized
from agents_service.config import Settings, load_settings
from agents_service.db import Database
from agents_service.routers import assistant, health
from agents_service.store import MySQLStore


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings if settings is not None else load_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # El pool se abre al primer uso (el health no necesita BD) y se cierra al apagar.
        yield
        await app.state.db.close()

    app = FastAPI(title="Telintec agents", docs_url=None, redoc_url=None, lifespan=lifespan)
    app.state.settings = settings
    app.state.db = Database(settings)
    app.state.store = MySQLStore(app.state.db, settings.db_agents)
    app.state.verifier = TokenVerifier(
        settings.token_keys_dir,
        settings.token_kids,
        settings.token_leeway_seconds,
        settings.token_max_lifetime_seconds,
    )

    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=list(settings.cors_origins),
            allow_methods=["GET", "POST", "OPTIONS"],
            allow_headers=["Authorization", "Content-Type", "X-Page-Context"],
            max_age=600,
        )

    @app.exception_handler(Unauthorized)
    async def _unauthorized(_: Request, exc: Unauthorized) -> JSONResponse:
        return JSONResponse({"data": None, "msg": UNAUTHORIZED_MSG, "error": exc.error}, status_code=401)

    app.include_router(health.router, prefix="/agents")
    app.include_router(assistant.router, prefix="/agents/assistant")
    return app


app = create_app()
