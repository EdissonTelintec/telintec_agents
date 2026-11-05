# -*- coding: utf-8 -*-
"""Webhook de Telegram del agente de ventas: ver, poner o quitar.

    python scripts/telegram_webhook.py info
    python scripts/telegram_webhook.py set --yes      # TELEGRAM_WEBHOOK_URL + TELEGRAM_WEBHOOK_SECRET del .env
    python scripts/telegram_webhook.py delete --yes

`set` y `delete` cambian a donde manda Telegram los mensajes del bot en vivo: piden --yes.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agents_service.channels.telegram import TelegramClient  # noqa: E402
from agents_service.config import load_settings  # noqa: E402


async def main(action: str, yes: bool) -> int:
    settings = load_settings()
    if not settings.telegram_token:
        print("falta TELEGRAM_TOKEN en el .env")
        return 2
    client = TelegramClient(settings.telegram_token)
    try:
        info = await client.get_webhook_info()
        print("webhook actual:", info.get("url") or "(ninguno)", "· pendientes:", info.get("pending_update_count"),
              "· último error:", info.get("last_error_message") or "-")
        if action == "info":
            return 0
        if not yes:
            print("agrega --yes para confirmar: cambia el destino de los mensajes del bot en vivo")
            return 1
        if action == "set":
            if not settings.telegram_webhook_secret:
                print("falta TELEGRAM_WEBHOOK_SECRET en el .env")
                return 2
            await client.set_webhook(settings.telegram_webhook_url, settings.telegram_webhook_secret)
            print("webhook puesto en", settings.telegram_webhook_url)
        elif action == "delete":
            await client.delete_webhook()
            print("webhook borrado")
        info = await client.get_webhook_info()
        print("webhook ahora:", info.get("url") or "(ninguno)")
        return 0
    finally:
        await client.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["info", "set", "delete"])
    parser.add_argument("--yes", action="store_true")
    args = parser.parse_args()
    raise SystemExit(asyncio.run(main(args.action, args.yes)))
