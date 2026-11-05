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
    model: str
    model_guardrail: str
    # HTTP
    cors_origins: tuple[str, ...]
    # Topes del agente publico
    limit_messages_per_conversation: int
    limit_conversations_per_ip_day: int
    limit_tokens_per_day_sales: int
    limit_output_tokens: int
    # Ventas
    sales_whatsapp_url: str
    sales_emails: tuple[str, ...]


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
        model=str(get("OPENAI_MODEL", "gpt-5.4-mini")),
        model_guardrail=str(get("OPENAI_MODEL_GUARDRAIL", "gpt-5.4-nano")),
        cors_origins=_split(get("CORS_ORIGINS")),
        limit_messages_per_conversation=int(get("LIMIT_MESSAGES_PER_CONVERSATION", "30") or 30),
        limit_conversations_per_ip_day=int(get("LIMIT_CONVERSATIONS_PER_IP_DAY", "20") or 20),
        limit_tokens_per_day_sales=int(get("LIMIT_TOKENS_PER_DAY_SALES", "3000000") or 3000000),
        limit_output_tokens=int(get("LIMIT_OUTPUT_TOKENS", "600") or 600),
        sales_whatsapp_url=str(get("SALES_WHATSAPP_URL", "https://wa.me/message/TBYVN75NGL4JJ1")),
        sales_emails=_split(get("SALES_EMAILS")),
    )
