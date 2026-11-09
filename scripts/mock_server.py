# -*- coding: utf-8 -*-
"""Servidor simulado de los agentes para el front: sin `.env`, sin OpenAI, sin MySQL.

    python scripts/mock_server.py                      # http://127.0.0.1:8100/agents
    python scripts/mock_server.py --port 8200 --delay 0
    python scripts/mock_server.py --origin http://mi-pc.local:3000

En la webapp: `NEXT_PUBLIC_AGENTS_URL=http://127.0.0.1:8100/agents`. Detalle en `agents_service/mock.py`.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import uvicorn  # noqa: E402

from agents_service.mock import DEFAULT_DELAY, SCENARIOS_HELP, create_mock_app  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Servidor simulado de los agentes de Telintec (para el front).")
    parser.add_argument("--host", default="127.0.0.1", help="0.0.0.0 para abrirlo a la red local")
    parser.add_argument("--port", type=int, default=8100)
    parser.add_argument("--delay", type=float, default=DEFAULT_DELAY, help="segundos entre palabras del stream")
    parser.add_argument("--origin", action="append", default=[], help="origen extra para CORS (localhost ya pasa)")
    args = parser.parse_args()

    base = f"http://{'127.0.0.1' if args.host == '0.0.0.0' else args.host}:{args.port}/agents"
    print(f"Agentes SIMULADOS en {base}")
    print(f"  ventas:     POST {base}/sales/chatkit (sin token)")
    print(f"  asistente:  POST {base}/assistant/chatkit (Authorization: <JWT crudo>, X-Page-Context: <ruta>)")
    print(f"  NEXT_PUBLIC_AGENTS_URL={base}")
    print("  " + SCENARIOS_HELP.replace("**", ""), flush=True)
    uvicorn.run(create_mock_app(delay=args.delay, origins=tuple(args.origin)), host=args.host, port=args.port)
    return 0


if __name__ == "__main__":
    sys.exit(main())
