# -*- coding: utf-8 -*-
"""Polling de Telegram para desarrollo (sin webhook): corre el agente de ventas contra la BD del .env.

    python scripts/telegram_polling.py

Se niega a arrancar si el bot tiene un webhook configurado (Telegram no permite las dos cosas);
borrarlo es `python scripts/telegram_webhook.py delete --yes` y afecta a quien lo tenga en uso.
"""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agents_service.agents.sales import build_sales_agent, fixed_text  # noqa: E402
from agents_service.channels.telegram import TelegramChannel, TelegramClient  # noqa: E402
from agents_service.config import load_settings  # noqa: E402
from agents_service.db import Database  # noqa: E402
from agents_service.limits import Limits  # noqa: E402
from agents_service.store import MySQLStore  # noqa: E402


async def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    settings = load_settings()
    if not settings.telegram_token:
        print("falta TELEGRAM_TOKEN en el .env")
        return 2
    db = Database(settings)
    client = TelegramClient(settings.telegram_token)
    try:
        me = await client.get_me()
        print(f"bot @{me.get('username')} · entorno {settings.environment} · Ctrl+C para salir")
        channel = TelegramChannel(client, MySQLStore(db, settings.db_agents, settings.timezone), Limits(db, settings), settings,
                                  build_sales_agent(settings, db), fixed_text=lambda k: fixed_text(k, settings),
                                  session_hours=settings.telegram_session_hours)
        await channel.poll_forever()
    except KeyboardInterrupt:
        pass
    finally:
        await client.close()
        await db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
