# -*- coding: utf-8 -*-
"""Contexto de una peticion de chat: quien habla, por que canal y para que agente.

Es el `TContext` del Store y del servidor de ChatKit. Lo arma el router a partir de la
peticion (JWT, IP, encabezados) y viaja a las tools del agente.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

AGENT_SALES = 0
AGENT_ASSISTANT = 1

CHANNEL_WEB = 0
CHANNEL_TELEGRAM = 1
CHANNEL_WHATSAPP = 2
CHANNEL_FACEBOOK = 3
CHANNEL_INSTAGRAM = 4


def hash_ip(ip: str | None) -> str | None:
    """sha256 de la IP: suficiente para el tope por IP y dia sin guardar la IP."""
    return hashlib.sha256(ip.encode("utf-8")).hexdigest() if ip else None


@dataclass
class RequestContext:
    agent: int
    channel: int = CHANNEL_WEB
    user_ref: str | None = None  # emp_id del JWT (asistente) o id del usuario del canal; None = visitante web
    ip_hash: str | None = None
    page_context: str | None = None
    token_data: dict = field(default_factory=dict)  # claims del JWT (solo asistente)
