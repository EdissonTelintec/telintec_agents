# -*- coding: utf-8 -*-
"""Guardrail de tema compartido por los agentes: un agente con el modelo nano clasifica el ultimo
mensaje del usuario y, si no es del tema, dispara el tripwire (el servidor de ChatKit responde el
texto fijo "off_topic"). Si el guardia falla (modelo sin acceso, red), deja pasar: el agente
principal ya tiene sus propias reglas en el prompt.
"""

from __future__ import annotations

import logging
from typing import Any

from agents import Agent, GuardrailFunctionOutput, InputGuardrail, ModelSettings, RunContextWrapper, Runner, input_guardrail
from agents.models.interface import Model
from pydantic import BaseModel, Field


class TopicVerdict(BaseModel):
    on_topic: bool = Field(description="true si el mensaje entra en el tema que atiende el agente")
    reason: str = Field(description="una frase")


def last_user_text(input_items: str | list[Any]) -> str:
    """Texto del ultimo mensaje del usuario en la entrada del agente (str o lista de items)."""
    if isinstance(input_items, str):
        return input_items
    for item in reversed(input_items):
        if isinstance(item, dict) and item.get("role") == "user":
            content = item.get("content")
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                texts = [c.get("text", "") for c in content if isinstance(c, dict) and c.get("type") in ("input_text", "text")]
                if texts:
                    return "\n".join(texts)
    return ""


def build_topic_guardrail(name: str, instructions: str, model: Model, log: logging.Logger, max_tokens: int = 80) -> InputGuardrail[Any]:
    guard_agent = Agent[Any](
        name=name,
        instructions=instructions,
        output_type=TopicVerdict,
        model=model,
        model_settings=ModelSettings(max_tokens=max_tokens),
    )

    @input_guardrail
    async def tema_guardrail(ctx: RunContextWrapper[Any], agent: Agent[Any], input_items: str | list[Any]) -> GuardrailFunctionOutput:
        text = last_user_text(input_items).strip()
        if not text or len(text) < 3:
            return GuardrailFunctionOutput(output_info=None, tripwire_triggered=False)
        try:
            result = await Runner.run(guard_agent, text[:1000], context=ctx.context)
            verdict = result.final_output_as(TopicVerdict)
        except Exception as e:  # noqa: BLE001 - si el guardia falla, no se bloquea al usuario
            log.warning("guardrail fallo: %s", e)
            return GuardrailFunctionOutput(output_info=None, tripwire_triggered=False)
        return GuardrailFunctionOutput(output_info=verdict, tripwire_triggered=not verdict.on_topic)

    return tema_guardrail
