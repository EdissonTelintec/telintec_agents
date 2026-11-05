# -*- coding: utf-8 -*-
"""Base de conocimiento del asistente de la webapp: `knowledge/help/<modulo>.md`.

Cada archivo trae un encabezado (front matter simple, una clave por linea entre dos `---`):
`modulo`, `titulo`, `rutas` (prefijos de la webapp, separados por coma), `permisos` (nombres del
catalogo con los que se ve el modulo) y `resumen` (una linea para el indice). El formato completo
esta en `knowledge/help/README.md`.

`HelpBase` carga la carpeta una vez por proceso: resuelve el modulo de una ruta (`X-Page-Context`)
por el prefijo mas largo, arma el indice para el prompt y entrega el texto de un modulo a la tool
`leer_guia`. Un archivo mal formado se omite con aviso en el log: el servicio no deja de arrancar
por una guia.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from agents_service.auth import ADMINISTRATOR
from agents_service.config import ROOT

log = logging.getLogger("agents.knowledge")

HELP_DIR = ROOT / "knowledge" / "help"
_REQUIRED_KEYS = ("modulo", "titulo", "rutas")


@dataclass(frozen=True)
class HelpDoc:
    slug: str
    title: str
    routes: tuple[str, ...]
    permissions: tuple[str, ...]  # vacio = lo ve cualquiera con sesion
    summary: str
    body: str
    path: Path

    def allows(self, permissions: Iterable[str]) -> bool:
        owned = set(permissions)
        return ADMINISTRATOR in owned or not self.permissions or any(p in owned for p in self.permissions)


def _split_list(value: str | None) -> tuple[str, ...]:
    return tuple(v.strip() for v in (value or "").split(",") if v.strip())


def split_front_matter(text: str) -> tuple[dict[str, str], str]:
    """Separa el encabezado `---` del cuerpo. Lanza ValueError si falta o no cierra."""
    lines = text.replace("\r\n", "\n").split("\n")
    if not lines or lines[0].strip() != "---":
        raise ValueError("falta el encabezado '---'")
    meta: dict[str, str] = {}
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return meta, "\n".join(lines[i + 1 :]).strip()
        if ":" in line:
            key, value = line.split(":", 1)
            meta[key.strip().lower()] = value.strip()
    raise ValueError("el encabezado '---' no cierra")


def normalize_route(route: str | None) -> str | None:
    """Ruta de la webapp sin query, sin diagonal final y acotada; None si no parece una ruta."""
    if not route:
        return None
    value = route.strip().split("?", 1)[0].split("#", 1)[0]
    if not value.startswith("/") or len(value) > 200:
        return None
    return value.rstrip("/") or "/"


def parse_help_doc(path: Path) -> HelpDoc:
    meta, body = split_front_matter(path.read_text(encoding="utf-8"))
    missing = [k for k in _REQUIRED_KEYS if not meta.get(k)]
    if missing:
        raise ValueError(f"faltan claves en el encabezado: {', '.join(missing)}")
    slug = meta["modulo"].strip().lower()
    if slug != path.stem.lower():
        raise ValueError(f"'modulo: {slug}' no coincide con el nombre del archivo {path.name}")
    routes = tuple(r for r in (normalize_route(x) for x in _split_list(meta["rutas"])) if r)
    if not routes:
        raise ValueError("'rutas' no trae ninguna ruta valida (deben empezar con /)")
    return HelpDoc(
        slug=slug,
        title=meta["titulo"],
        routes=routes,
        permissions=_split_list(meta.get("permisos")),
        summary=meta.get("resumen", ""),
        body=body,
        path=path,
    )


class HelpBase:
    def __init__(self, docs: Iterable[HelpDoc]):
        self.docs: list[HelpDoc] = sorted(docs, key=lambda d: d.slug)
        self._by_slug = {d.slug: d for d in self.docs}
        # prefijo mas largo primero; a igual largo, el slug alfabetico (determinista)
        self._routes = sorted(((r, d.slug) for d in self.docs for r in d.routes), key=lambda x: (-len(x[0]), x[1]))

    @classmethod
    def load(cls, directory: Path = HELP_DIR) -> HelpBase:
        docs: list[HelpDoc] = []
        if directory.is_dir():
            for path in sorted(directory.glob("*.md")):
                if path.name.lower() == "readme.md":
                    continue
                try:
                    docs.append(parse_help_doc(path))
                except (ValueError, OSError, UnicodeDecodeError) as e:
                    log.warning("guia %s omitida: %s", path.name, e)
        else:
            log.warning("no existe la carpeta de guias %s", directory)
        return cls(docs)

    def __len__(self) -> int:
        return len(self.docs)

    @property
    def slugs(self) -> list[str]:
        return [d.slug for d in self.docs]

    def get(self, slug: str | None) -> HelpDoc | None:
        return self._by_slug.get((slug or "").strip().lower())

    def module_for_route(self, route: str | None) -> HelpDoc | None:
        """La guia cuyo prefijo mas largo cubre la ruta; None si ninguna la cubre."""
        value = normalize_route(route)
        if value is None:
            return None
        for prefix, slug in self._routes:
            if value == prefix or value.startswith(prefix + "/"):
                return self._by_slug[slug]
        return None

    def accessible(self, permissions: Iterable[str]) -> list[HelpDoc]:
        owned = list(permissions)
        return [d for d in self.docs if d.allows(owned)]

    def index_text(self, permissions: Iterable[str] | None = None) -> str:
        """Una linea por modulo para el prompt; marca los que el usuario no puede abrir."""
        owned = list(permissions) if permissions is not None else None
        lines = []
        for d in self.docs:
            access = "" if owned is None or d.allows(owned) else " [el usuario NO tiene acceso]"
            summary = f": {d.summary}" if d.summary else ""
            lines.append(f"- `{d.slug}` — {d.title} (rutas {', '.join(d.routes)}){summary}{access}")
        return "\n".join(lines)
