# -*- coding: utf-8 -*-
"""Agente del asistente sin tocar OpenAI: prompt segun el contexto, tools, textos fijos."""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest
from agents import FileSearchTool, FunctionTool, RunContextWrapper
from agents.tool_context import ToolContext

from agents_service.agents.assistant import (
    AGENT_NAME,
    ERROR_TEXT,
    LIMIT_TEXT,
    OFF_TOPIC_TEXT,
    build_assistant_agent,
    build_instructions,
    fixed_text,
)
from agents_service.context import AGENT_ASSISTANT, RequestContext
from agents_service.knowledge import HelpBase

DOC_RRHH = """---
modulo: rrhh
titulo: RRHH
rutas: /dashboard/rrhh
permisos: App.Department.RRHH
resumen: Personal y nómina.
---
# RRHH

## Personal (`/dashboard/rrhh/personal`)
- **Cómo se usa:** haz clic en **Nuevo empleado**.
"""

DOC_COMUN = """---
modulo: comun
titulo: Común
rutas: /dashboard/comun
permisos: App.Department.Common, App.Department.Basic
resumen: Check-in y tareas.
---
# Común
"""


@pytest.fixture
def base(tmp_path: Path) -> HelpBase:
    (tmp_path / "rrhh.md").write_text(DOC_RRHH, encoding="utf-8")
    (tmp_path / "comun.md").write_text(DOC_COMUN, encoding="utf-8")
    return HelpBase.load(tmp_path)


def test_instructions_by_context(settings, base: HelpBase):
    ctx = RequestContext(
        agent=AGENT_ASSISTANT,
        user_ref="emp:7",
        page_context="/dashboard/rrhh/personal/editar",
        token_data={"name": "Ana P", "permissions": {"0": "App.Department.RRHH"}},
    )
    text = build_instructions(settings, base, ctx)
    assert "Nombre: Ana P" in text and "Permisos: App.Department.RRHH" in text
    assert "módulo **RRHH** (guía `rrhh`)" in text and "## Guía de la pantalla actual: RRHH" in text and "**Nuevo empleado**" in text
    assert "Módulos a los que puede entrar: RRHH" in text
    assert "`comun` — Común" in text and "[el usuario NO tiene acceso]" in text
    assert "file_search" not in text  # sin vector store
    text2 = build_instructions(settings, base, None)
    assert "No sé en qué pantalla está" in text2 and "## Guía de la pantalla actual" not in text2
    text3 = build_instructions(settings, base, RequestContext(agent=AGENT_ASSISTANT, page_context="/dashboard/zzz", token_data={}))
    assert "ninguna guía la cubre" in text3 and "Nombre: usuario" in text3


async def test_agent_tools_and_dynamic_prompt(settings, base: HelpBase):
    s = dataclasses.replace(settings, openai_api_key_assistant="sk-prueba", openai_vector_store_id="vs_123")
    agent = build_assistant_agent(s, base)
    assert agent.name == AGENT_NAME and len(agent.input_guardrails) == 1
    assert [t.name for t in agent.tools if isinstance(t, FunctionTool)] == ["leer_guia"]
    assert any(isinstance(t, FileSearchTool) and t.vector_store_ids == ["vs_123"] for t in agent.tools)
    tool = next(t for t in agent.tools if isinstance(t, FunctionTool))

    async def invoke(modulo: str) -> dict:
        args = json.dumps({"modulo": modulo})
        ctx = ToolContext(context=cast(Any, None), tool_name="leer_guia", tool_call_id="c1", tool_arguments=args)
        return cast(dict, await tool.on_invoke_tool(ctx, args))

    out = await invoke("RRHH")
    assert out["modulo"] == "rrhh" and "**Nuevo empleado**" in out["texto"] and out["rutas"] == ["/dashboard/rrhh"]
    missing = await invoke("nada")
    assert "error" in missing and missing["modulos"] == ["comun", "rrhh"]
    # instrucciones dinamicas con el contexto que arma el servidor de ChatKit
    fake = SimpleNamespace(
        request_context=RequestContext(agent=AGENT_ASSISTANT, page_context="/dashboard/comun/checkin", token_data={"name": "Luis"})
    )
    text = await agent.get_system_prompt(RunContextWrapper(context=cast(Any, fake)))
    assert text and "Nombre: Luis" in text and "módulo **Común**" in text and "file_search" in text
    # sin vector store no hay File Search
    plain = build_assistant_agent(dataclasses.replace(settings, openai_api_key_assistant="sk-prueba"), base)
    assert not any(isinstance(t, FileSearchTool) for t in plain.tools)


def test_fixed_texts_and_key(settings, base: HelpBase):
    assert fixed_text("off_topic", settings) == OFF_TOPIC_TEXT
    assert fixed_text("limit", settings) == LIMIT_TEXT
    assert fixed_text("otro", settings) == ERROR_TEXT
    with pytest.raises(RuntimeError):
        build_assistant_agent(settings, base)
