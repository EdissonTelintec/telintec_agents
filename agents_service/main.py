# -*- coding: utf-8 -*-
"""App FastAPI del servicio. `uvicorn agents_service.main:app` en prod; `create_app` en pruebas."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from agents_service.agents.sales import build_sales_agent, fixed_text
from agents_service.auth import UNAUTHORIZED_MSG, TokenVerifier, Unauthorized
from agents_service.chat import TelintecChatKitServer
from agents_service.config import Settings, load_settings
from agents_service.db import Database
from agents_service.limits import Limits
from agents_service.routers import assistant, health, sales
from agents_service.store import MySQLStore

log = logging.getLogger("agents")

PRODUCT_IMAGE_DOMAINS = ["ftp3.syscom.mx"]


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
    app.state.store = MySQLStore(app.state.db, settings.db_agents, settings.timezone)
    app.state.limits = Limits(app.state.db, settings)
    app.state.verifier = TokenVerifier(
        settings.token_keys_dir,
        settings.token_kids,
        settings.token_leeway_seconds,
        settings.token_max_lifetime_seconds,
    )

    # Agente virtual de ventas: un solo agente por proceso (las tools cierran sobre db y settings).
    app.state.sales_server = None
    if settings.openai_api_key_sales:
        from agents import set_tracing_export_api_key

        set_tracing_export_api_key(settings.openai_api_key_sales)
        sales_agent = build_sales_agent(settings, app.state.db)
        app.state.sales_server = TelintecChatKitServer(
            app.state.store,
            settings,
            app.state.limits,
            agent_factory=lambda _ctx: sales_agent,
            fixed_text=lambda kind: fixed_text(kind, settings),
            allowed_image_domains=PRODUCT_IMAGE_DOMAINS,
        )
        app.state.telegram_channel = None
        if settings.telegram_token:
            from agents_service.channels.telegram import TelegramChannel, TelegramClient

            app.state.telegram_channel = TelegramChannel(
                TelegramClient(settings.telegram_token),
                app.state.store,
                app.state.limits,
                settings,
                sales_agent,
                fixed_text=lambda kind: fixed_text(kind, settings),
                session_hours=settings.telegram_session_hours,
            )
    else:
        app.state.telegram_channel = None
        log.warning("OPENAI_API_KEY_SALES no esta: /agents/sales/chatkit respondera 503")

    # Asistente de la webapp (F3): mismo servidor de ChatKit con el agente de knowledge/help/.
    app.state.assistant_server = None
    app.state.help_base = None
    if settings.openai_api_key_assistant:
        from agents import set_tracing_export_api_key

        from agents_service.agents.assistant import GuideCitationConverter, build_assistant_agent
        from agents_service.agents.assistant import fixed_text as assistant_fixed_text
        from agents_service.knowledge import HelpBase

        help_base = HelpBase.load()
        if not len(help_base):
            log.warning("knowledge/help/ sin guias validas: el asistente solo sabra lo que dice su prompt")
        app.state.help_base = help_base
        assistant_agent = build_assistant_agent(settings, help_base)
        app.state.assistant_server = TelintecChatKitServer(
            app.state.store,
            settings,
            app.state.limits,
            agent_factory=lambda _ctx: assistant_agent,
            fixed_text=lambda kind: assistant_fixed_text(kind, settings),
            converter=GuideCitationConverter(help_base),
        )
        if not settings.openai_api_key_sales:
            # la llave de traces del SDK es global: con las dos llaves se exporta con la de ventas
            set_tracing_export_api_key(settings.openai_api_key_assistant)
    else:
        log.warning("OPENAI_API_KEY_ASSISTANT no esta: /agents/assistant/chatkit respondera 503")

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
    app.include_router(sales.router, prefix="/agents/sales")
    app.include_router(assistant.router, prefix="/agents/assistant")
    return app


app = create_app()
