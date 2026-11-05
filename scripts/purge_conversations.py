# -*- coding: utf-8 -*-
"""Borra las conversaciones sin solicitud de cotizacion con mas de 90 dias (retencion, D8).

    python scripts/purge_conversations.py [--days 90] [--dry-run]

Pensado para un timer de systemd diario junto al del catalogo.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agents_service.config import load_settings  # noqa: E402
from agents_service.db import Database  # noqa: E402
from agents_service.retention import purge_conversations  # noqa: E402


async def main(days: int, dry_run: bool) -> int:
    settings = load_settings()
    db = Database(settings)
    now = datetime.now(ZoneInfo(settings.timezone)).replace(tzinfo=None)
    try:
        if dry_run:
            row = await db.fetch_one(
                f"SELECT COUNT(*) AS n FROM {settings.db_agents}.agent_conversations c "
                f"LEFT JOIN {settings.db_agents}.agent_quote_requests q ON q.conversation_id = c.conversation_id "
                "WHERE q.request_id IS NULL AND c.created_at < DATE_SUB(%s, INTERVAL %s DAY)",
                (now, days),
            )
            n = int(row["n"]) if row else 0
            print(f"[dry-run] se borrarian {n} conversaciones de mas de {days} dias")
        else:
            n = await purge_conversations(db, now, days, settings.db_agents)
            print(f"borradas {n} conversaciones de mas de {days} dias")
    finally:
        await db.close()
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=90)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    raise SystemExit(asyncio.run(main(args.days, args.dry_run)))
