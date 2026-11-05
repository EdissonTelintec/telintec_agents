# -*- coding: utf-8 -*-
"""Topes del agente publico y contabilidad de tokens (docs/agentes_openai.md del API, D10).

- mensajes del visitante por conversacion (`agent_messages` de tipo user_message);
- conversaciones nuevas por IP y dia (`agent_conversations.ip_hash` + `created_at`);
- tokens por dia y agente (`agent_usage_daily`).

Los dias se cuentan en la zona del servicio (hora del centro de Mexico). Al pasar un tope el
agente responde con un texto fijo sin llamar al modelo.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from agents_service.config import Settings
from agents_service.context import RequestContext
from agents_service.db import Database

REASON_MESSAGES = "messages_per_conversation"
REASON_IP = "conversations_per_ip_day"
REASON_TOKENS = "tokens_per_day"


@dataclass(frozen=True)
class LimitCheck:
    ok: bool
    reason: str | None = None


class Limits:
    def __init__(self, db: Database, settings: Settings, schema: str | None = None):
        self._db = db
        self._s = settings
        self._schema = schema or settings.db_agents
        self._tz = ZoneInfo(settings.timezone)

    def now(self) -> datetime:
        return datetime.now(self._tz).replace(tzinfo=None)

    def today_bounds(self) -> tuple[datetime, datetime]:
        start = self.now().replace(hour=0, minute=0, second=0, microsecond=0)
        return start, start + timedelta(days=1)

    async def user_messages(self, conversation_id: str) -> int:
        row = await self._db.fetch_one(
            f"SELECT COUNT(*) AS n FROM {self._schema}.agent_messages "
            "WHERE conversation_id = %s AND item_type = 'user_message'",
            (conversation_id,),
        )
        return int(row["n"]) if row else 0

    async def conversations_today(self, ip_hash: str) -> int:
        start, end = self.today_bounds()
        row = await self._db.fetch_one(
            f"SELECT COUNT(*) AS n FROM {self._schema}.agent_conversations "
            "WHERE ip_hash = %s AND created_at >= %s AND created_at < %s",
            (ip_hash, start, end),
        )
        return int(row["n"]) if row else 0

    async def tokens_today(self, agent: int) -> int:
        row = await self._db.fetch_one(
            f"SELECT tokens_in + tokens_out AS n FROM {self._schema}.agent_usage_daily WHERE day = %s AND agent = %s",
            (self.now().date(), agent),
        )
        return int(row["n"]) if row and row["n"] is not None else 0

    async def check(self, context: RequestContext, conversation_id: str, is_new_conversation: bool) -> LimitCheck:
        """Orden: presupuesto del dia, conversaciones por IP (solo al abrir una), mensajes del hilo."""
        if await self.tokens_today(context.agent) >= self._s.limit_tokens_per_day_sales:
            return LimitCheck(False, REASON_TOKENS)
        if is_new_conversation and context.ip_hash:
            # la conversacion nueva ya esta guardada cuando se llama: cuenta ella misma
            if await self.conversations_today(context.ip_hash) > self._s.limit_conversations_per_ip_day:
                return LimitCheck(False, REASON_IP)
        if await self.user_messages(conversation_id) > self._s.limit_messages_per_conversation:
            return LimitCheck(False, REASON_MESSAGES)
        return LimitCheck(True)

    async def record_usage(self, agent: int, conversation_id: str, tokens_in: int, tokens_out: int) -> None:
        if tokens_in <= 0 and tokens_out <= 0:
            return
        await self._db.execute(
            f"UPDATE {self._schema}.agent_conversations SET tokens_in = tokens_in + %s, tokens_out = tokens_out + %s "
            "WHERE conversation_id = %s",
            (tokens_in, tokens_out, conversation_id),
        )
        await self._db.execute(
            f"INSERT INTO {self._schema}.agent_usage_daily (day, agent, turns, tokens_in, tokens_out) "
            "VALUES (%s, %s, 1, %s, %s) AS new "
            "ON DUPLICATE KEY UPDATE turns = agent_usage_daily.turns + 1, "
            "tokens_in = agent_usage_daily.tokens_in + new.tokens_in, tokens_out = agent_usage_daily.tokens_out + new.tokens_out",
            (self.now().date(), agent, tokens_in, tokens_out),
        )
