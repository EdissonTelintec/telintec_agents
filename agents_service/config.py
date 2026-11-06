# -*- coding: utf-8 -*-
"""Configuracion del servicio.

Fuentes, en este orden: variable del sistema > `.env` del repo > `../.env`. Igual que el API
(GUITelintec/docs/entorno_desde_env.md), `AGENTS_ENVIRONMENT` no tiene valor por defecto: sin
`dev` o `prod` el servicio no arranca. Las llaves publicas de los tokens se leen de la carpeta
del `.env` encontrado (`token_public_<kid>.pem`) salvo que `TOKEN_PUBLIC_KEYS_DIR` diga otra.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parent.parent

_REQUIRED = ("DB_HOST", "DB_USER", "DB_PASSWORD")


def find_env_file(start: Path = ROOT) -> Path | None:
    """`.env` del repo, o el de la carpeta padre (prod lo guarda fuera del checkout)."""
    for candidate in (start / ".env", start.parent / ".env"):
        if candidate.is_file():
            return candidate
    return None


@dataclass(frozen=True)
class Settings:
    environment: str  # "dev" | "prod"
    env_file: Path | None
    # MySQL (usuario agents_svc: SELECT en el catalogo, DML en sql_telintec_mod_agents)
    db_host: str
    db_port: int
    db_user: str
    db_password: str
    db_catalog: str
    db_agents: str
    db_pool_size: int
    # Tokens ES256 del login (mismas llaves publicas que el API)
    token_keys_dir: Path
    token_kids: tuple[str, ...]
    token_leeway_seconds: int
    token_max_lifetime_seconds: int
    # OpenAI (un proyecto por agente)
    openai_api_key_sales: str | None
    openai_api_key_assistant: str | None
    openai_vector_store_id: str | None  # File Search del asistente (scripts/sync_kb.py); vacio = solo guias locales
    model: str
    model_guardrail: str
    # HTTP
    cors_origins: tuple[str, ...]
    # Topes del agente publico
    limit_messages_per_conversation: int
    limit_conversations_per_ip_day: int
    limit_tokens_per_day_sales: int
    limit_output_tokens: int
    limit_tokens_per_day_assistant: int  # presupuesto diario del asistente de la webapp
    limit_output_tokens_assistant: int
    # Ventas y correo (SES: misma identidad remitente que el API)
    sales_whatsapp_url: str
    sales_emails: tuple[str, ...]
    ses_region: str | None
    ses_sender: str | None
    quote_notify_apps: tuple[str, ...]  # claves de `body.app` de la notificacion interna de una solicitud
    trust_proxy: bool  # True detras de nginx: la IP sale de X-Forwarded-For
    # Telegram (F2)
    telegram_token: str | None
    telegram_webhook_secret: str | None
    telegram_webhook_url: str
    telegram_session_hours: int
    # Sincronizacion del catalogo SYSCOM (scripts/sync_catalog.py; docs/catalogo_syscom_sync.md del API)
    catalog_db_user: str | None
    catalog_db_password: str | None
    syscom_client_id: str | None
    syscom_client_secret: str | None
    s3_catalog_bucket: str | None
    timezone: str  # hora del centro de Mexico para las fechas que escribe el servicio


def _split(value: str | None) -> tuple[str, ...]:
    return tuple(v.strip() for v in (value or "").split(",") if v.strip())


def load_settings(env_file: Path | None = None, environ: Mapping[str, str] | None = None) -> Settings:
    """Arma `Settings`. `env_file` fuerza un archivo (si no existe, solo cuentan las variables);
    `environ` reemplaza `os.environ` (pruebas)."""
    environ = os.environ if environ is None else environ
    path = env_file if env_file is not None else find_env_file()
    values: dict[str, str | None] = dict(dotenv_values(path)) if path is not None and path.is_file() else {}

    def get(key: str, default: str | None = None) -> str | None:
        value = environ.get(key)
        if value is None or value == "":
            value = values.get(key)
        return default if value is None or value == "" else value

    environment = get("AGENTS_ENVIRONMENT")
    if environment not in ("dev", "prod"):
        raise RuntimeError(
            "AGENTS_ENVIRONMENT debe ser 'dev' o 'prod' (variable del sistema o llave del .env); "
            f"valor: {environment!r}, .env: {path}"
        )
    missing = [k for k in _REQUIRED if get(k) is None]
    if missing:
        raise RuntimeError(f"Faltan en el .env o el entorno: {', '.join(missing)}")

    keys_dir = get("TOKEN_PUBLIC_KEYS_DIR")
    default_kids = ("lambda",) + (("dev",) if environment == "dev" else ())
    return Settings(
        environment=environment,
        env_file=path if path is not None and path.is_file() else None,
        db_host=str(get("DB_HOST")),
        db_port=int(get("DB_PORT", "3306") or 3306),
        db_user=str(get("DB_USER")),
        db_password=str(get("DB_PASSWORD")),
        db_catalog=str(get("DB_CATALOG", "sql_telintec")),
        db_agents=str(get("DB_AGENTS", "sql_telintec_mod_agents")),
        db_pool_size=int(get("DB_POOL_SIZE", "5") or 5),
        token_keys_dir=Path(keys_dir) if keys_dir else (path.parent if path is not None else ROOT),
        token_kids=_split(get("TOKEN_PUBLIC_KIDS")) or default_kids,
        token_leeway_seconds=int(get("TOKEN_LEEWAY_SECONDS", "30") or 30),
        token_max_lifetime_seconds=int(get("TOKEN_MAX_LIFETIME_SECONDS", str(24 * 60 * 60)) or 24 * 60 * 60),
        openai_api_key_sales=get("OPENAI_API_KEY_SALES"),
        openai_api_key_assistant=get("OPENAI_API_KEY_ASSISTANT"),
        openai_vector_store_id=get("OPENAI_VECTOR_STORE_ID"),
        model=str(get("OPENAI_MODEL", "gpt-5.4-mini")),
        model_guardrail=str(get("OPENAI_MODEL_GUARDRAIL", "gpt-6-luna")),
        cors_origins=_split(get("CORS_ORIGINS")),
        limit_messages_per_conversation=int(get("LIMIT_MESSAGES_PER_CONVERSATION", "30") or 30),
        limit_conversations_per_ip_day=int(get("LIMIT_CONVERSATIONS_PER_IP_DAY", "20") or 20),
        limit_tokens_per_day_sales=int(get("LIMIT_TOKENS_PER_DAY_SALES", "3000000") or 3000000),
        limit_output_tokens=int(get("LIMIT_OUTPUT_TOKENS", "1000") or 1000),
        limit_tokens_per_day_assistant=int(get("LIMIT_TOKENS_PER_DAY_ASSISTANT", "1000000") or 1000000),
        limit_output_tokens_assistant=int(get("LIMIT_OUTPUT_TOKENS_ASSISTANT", "900") or 900),
        sales_whatsapp_url=str(get("SALES_WHATSAPP_URL", "https://wa.me/message/TBYVN75NGL4JJ1")),
        sales_emails=_split(get("SALES_EMAILS")),
        ses_region=get("SES_REGION"),
        ses_sender=get("SES_SENDER"),
        quote_notify_apps=_split(get("QUOTE_NOTIFY_APPS")) or ("administracion", "adminpreventa"),
        trust_proxy=(get("TRUST_PROXY", "0") or "0") not in ("0", "false", "False"),
        telegram_token=get("TELEGRAM_TOKEN"),
        telegram_webhook_secret=get("TELEGRAM_WEBHOOK_SECRET"),
        telegram_webhook_url=str(get("TELEGRAM_WEBHOOK_URL", "https://appinterna.telintec.mx/agents/sales/telegram")),
        telegram_session_hours=int(get("TELEGRAM_SESSION_HOURS", "24") or 24),
        catalog_db_user=get("CATALOG_DB_USER"),
        catalog_db_password=get("CATALOG_DB_PASSWORD"),
        syscom_client_id=get("SYSCOM_CLIENT_ID"),
        syscom_client_secret=get("SYSCOM_CLIENT_SECRET"),
        s3_catalog_bucket=get("S3_CATALOG_BUCKET"),
        timezone=str(get("SERVICE_TIMEZONE", "America/Mexico_City")),
    )
