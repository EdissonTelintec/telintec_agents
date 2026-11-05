# -*- coding: utf-8 -*-
"""Retencion (docs/agentes_openai.md del API, D8): las conversaciones sin solicitud de cotizacion
se borran a los 90 dias; las que tienen solicitud se conservan. `agent_messages` cae en cascada."""

from __future__ import annotations

from datetime import datetime, timedelta

from agents_service.db import Database


async def purge_conversations(db: Database, now: datetime, days: int = 90, schema: str = "sql_telintec_mod_agents") -> int:
    cutoff = now - timedelta(days=days)
    rows, _ = await db.execute(
        f"DELETE FROM {schema}.agent_conversations WHERE created_at < %s "
        f"AND conversation_id NOT IN (SELECT conversation_id FROM {schema}.agent_quote_requests)",
        (cutoff,),
    )
    return rows
