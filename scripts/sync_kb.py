# -*- coding: utf-8 -*-
"""Sube `knowledge/help/*.md` al vector store del proyecto del asistente (File Search).

    python scripts/sync_kb.py            # crea el vector store si hace falta y sube lo que cambio
    python scripts/sync_kb.py --dry-run  # solo dice que haria

Cada archivo va con `attributes` {path, sha256, modulo, titulo}: `path` lo identifica y `sha256`
detecta cambios; lo que ya no esta en la carpeta se borra del vector store y de Files. Si el `.env`
no trae OPENAI_VECTOR_STORE_ID busca un vector store llamado `telintec-webapp-help` en el proyecto
y, si no existe, lo crea e imprime el id para agregarlo al `.env` (el servicio lo lee al arrancar).
El asistente funciona sin vector store (guias locales); File Search solo suma busqueda por fragmentos.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from openai import OpenAI  # noqa: E402

from agents_service.config import load_settings  # noqa: E402
from agents_service.knowledge import HELP_DIR, parse_help_doc  # noqa: E402

VECTOR_STORE_NAME = "telintec-webapp-help"


def find_or_create_store(client: OpenAI, dry_run: bool) -> str | None:
    for vs in client.vector_stores.list():
        if vs.name == VECTOR_STORE_NAME:
            print(f"vector store '{VECTOR_STORE_NAME}' encontrado: {vs.id}")
            return vs.id
    if dry_run:
        print(f"[dry-run] crearia el vector store '{VECTOR_STORE_NAME}'")
        return None
    vs = client.vector_stores.create(name=VECTOR_STORE_NAME)
    print(f"vector store creado: {vs.id}  -> agrega OPENAI_VECTOR_STORE_ID={vs.id} al .env del servicio")
    return vs.id


def main(dry_run: bool) -> int:
    settings = load_settings()
    if not settings.openai_api_key_assistant:
        print("falta OPENAI_API_KEY_ASSISTANT en el .env")
        return 2
    local: dict[str, tuple[Path, str, str, str]] = {}  # path -> (archivo, sha256, modulo, titulo)
    for path in sorted(HELP_DIR.glob("*.md")):
        if path.name.lower() == "readme.md":
            continue
        try:
            doc = parse_help_doc(path)
        except ValueError as e:
            print(f"omitido {path.name}: {e}")
            continue
        local[path.name] = (path, hashlib.sha256(path.read_bytes()).hexdigest(), doc.slug, doc.title)
    if not local:
        print(f"no hay guias validas en {HELP_DIR}")
        return 1

    client = OpenAI(api_key=settings.openai_api_key_assistant)
    vs_id = settings.openai_vector_store_id or find_or_create_store(client, dry_run)
    if vs_id is None:
        print(f"[dry-run] subiria {len(local)} archivos: {', '.join(sorted(local))}")
        return 0

    remote: dict[str, tuple[str, str]] = {}  # path -> (vector_store_file_id, sha256)
    for f in client.vector_stores.files.list(vs_id):
        attrs = f.attributes or {}
        key = str(attrs.get("path") or f.id)
        remote[key] = (f.id, str(attrs.get("sha256") or ""))

    uploaded = replaced = deleted = unchanged = 0
    for name, (path, sha, slug, title) in local.items():
        old = remote.pop(name, None)
        if old and old[1] == sha:
            unchanged += 1
            continue
        action = "reemplazar" if old else "subir"
        if dry_run:
            print(f"[dry-run] {action} {name}")
            continue
        with path.open("rb") as fh:
            uploaded_file = client.files.create(file=(name, fh, "text/markdown"), purpose="assistants")
        client.vector_stores.files.create_and_poll(
            uploaded_file.id,
            vector_store_id=vs_id,
            attributes={"path": name, "sha256": sha, "modulo": slug, "titulo": title},
        )
        if old:
            client.vector_stores.files.delete(old[0], vector_store_id=vs_id)
            client.files.delete(old[0])
            replaced += 1
        else:
            uploaded += 1
        print(f"{action}: {name}")
    for name, (file_id, _) in remote.items():
        if dry_run:
            print(f"[dry-run] borrar {name}")
            continue
        client.vector_stores.files.delete(file_id, vector_store_id=vs_id)
        client.files.delete(file_id)
        deleted += 1
        print(f"borrado: {name}")
    print(f"listo: {uploaded} nuevos, {replaced} reemplazados, {deleted} borrados, {unchanged} sin cambios (vector store {vs_id})")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    raise SystemExit(main(args.dry_run))
