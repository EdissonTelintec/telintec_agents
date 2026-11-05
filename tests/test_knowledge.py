# -*- coding: utf-8 -*-
"""Base de conocimiento del asistente: encabezado, ruta -> modulo (prefijo mas largo), indice y acceso."""

from __future__ import annotations

from pathlib import Path

import pytest

from agents_service.knowledge import HELP_DIR, HelpBase, normalize_route, parse_help_doc, split_front_matter

DOC_SM = """---
modulo: sm
titulo: Solicitudes de Material
rutas: /dashboard/sm, /dashboard/operations/sm-approve
permisos: App.Department.SM, App.Department.smCreate
resumen: Crear y seguir solicitudes de material.
---
# Solicitudes de Material

## Solicitudes (`/dashboard/sm/solicitudes`)
- **Para qué sirve:** pedir material.
"""

DOC_OPS = """---
modulo: operaciones
titulo: Operaciones
rutas: /dashboard/operations
permisos: App.Department.Operaciones
resumen: Aprobaciones.
---
# Operaciones
"""


@pytest.fixture
def base(tmp_path: Path) -> HelpBase:
    (tmp_path / "sm.md").write_text(DOC_SM, encoding="utf-8")
    (tmp_path / "operaciones.md").write_text(DOC_OPS, encoding="utf-8")
    (tmp_path / "README.md").write_text("# formato", encoding="utf-8")
    (tmp_path / "roto.md").write_text("sin encabezado", encoding="utf-8")
    (tmp_path / "otro.md").write_text("---\nmodulo: distinto\ntitulo: X\nrutas: /a\n---\n", encoding="utf-8")
    return HelpBase.load(tmp_path)


def test_parse_and_skip_invalid(base: HelpBase, tmp_path: Path):
    assert base.slugs == ["operaciones", "sm"]  # README, roto y otro (modulo != archivo) quedan fuera
    doc = base.get("SM")
    assert doc and doc.title == "Solicitudes de Material"
    assert doc.routes == ("/dashboard/sm", "/dashboard/operations/sm-approve")
    assert doc.permissions == ("App.Department.SM", "App.Department.smCreate") and doc.body.startswith("# Solicitudes")
    with pytest.raises(ValueError):
        parse_help_doc(tmp_path / "roto.md")
    with pytest.raises(ValueError):
        parse_help_doc(tmp_path / "otro.md")


def test_front_matter_crlf_and_colons():
    meta, body = split_front_matter("---\r\nmodulo: a\r\ntitulo: B: con dos puntos\r\n---\r\ncuerpo\r\n")
    assert meta == {"modulo": "a", "titulo": "B: con dos puntos"} and body == "cuerpo"
    with pytest.raises(ValueError):
        split_front_matter("---\nmodulo: a\n")


def test_normalize_route():
    assert normalize_route("/dashboard/sm/?x=1#y") == "/dashboard/sm"
    assert normalize_route(" /dashboard/sm/sm-control/12 ") == "/dashboard/sm/sm-control/12"
    assert normalize_route("/") == "/"
    assert normalize_route("dashboard") is None and normalize_route("") is None and normalize_route(None) is None
    assert normalize_route("/" + "a" * 300) is None


def test_module_for_route_longest_prefix(base: HelpBase):
    def slug(route: str | None) -> str | None:
        doc = base.module_for_route(route)
        return doc.slug if doc else None

    assert slug("/dashboard/sm/sm-control/12?tab=1") == "sm"
    assert slug("/dashboard/operations/sm-approve") == "sm"  # el prefijo mas largo gana
    assert slug("/dashboard/operations/aproveVoucher") == "operaciones"
    assert slug("/dashboard/smx") is None and slug(None) is None


def test_access_and_index(base: HelpBase):
    assert [d.slug for d in base.accessible(["App.Department.smCreate"])] == ["sm"]
    assert [d.slug for d in base.accessible(["App.Department.Administrator"])] == ["operaciones", "sm"]
    text = base.index_text(["App.Department.SM"])
    lines = text.split("\n")
    assert lines[0].startswith("- `operaciones` — Operaciones (rutas /dashboard/operations): Aprobaciones.") and "NO tiene acceso" in lines[0]
    assert lines[1] == "- `sm` — Solicitudes de Material (rutas /dashboard/sm, /dashboard/operations/sm-approve): Crear y seguir solicitudes de material."
    assert "NO tiene acceso" not in base.index_text()


def test_repo_help_folder_is_valid():
    """Todas las guias del repo cargan (README no cuenta): un encabezado roto se nota aqui."""
    files = [p for p in HELP_DIR.glob("*.md") if p.name.lower() != "readme.md"]
    assert len(HelpBase.load(HELP_DIR)) == len(files)
