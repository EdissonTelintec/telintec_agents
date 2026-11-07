# -*- coding: utf-8 -*-
"""Guardrail de tema compartido por los agentes: un agente con el modelo del guardia
(`OPENAI_MODEL_GUARDRAIL`) clasifica el ultimo mensaje del usuario y, si no es del tema, dispara el
tripwire (el servidor de ChatKit responde el texto fijo "off_topic"). Corre ANTES del agente, no en
paralelo (el default del SDK): en paralelo, si el guardia tarda mas, el agente alcanza a contestar lo
fuera de tema (se transmite y se cobra) y despues llega el texto fijo. Si el guardia falla (modelo
sin acceso, red), deja pasar: el agente principal ya tiene sus propias reglas en el prompt.

El guardia recibe tambien el ultimo mensaje del agente como contexto: sin el, una respuesta corta a lo
que pregunto el agente ("Edisson, 8127668300", "ahi te pase los datos", "el segundo") parece fuera de
tema y el visitante se queda atorado en el texto fijo (paso en Telegram con gpt-5.4-nano, 2026-11-06).
"""

from __future__ import annotations

import logging
from typing import Any

from agents import Agent, GuardrailFunctionOutput, InputGuardrail, ModelSettings, RunContextWrapper, Runner, input_guardrail
from agents.models.interface import Model
from openai.types.shared import Reasoning
from pydantic import BaseModel, Field


class TopicVerdict(BaseModel):
    on_topic: bool = Field(description="true si el mensaje entra en el tema que atiende el agente")
    reason: str = Field(description="una frase")


CONTEXT_RULES = (
    "La entrada puede traer el último mensaje del agente como contexto; ese no se clasifica. Una respuesta a lo "
    "que el agente preguntó o propuso (sí o no, un número, un nombre, un teléfono o correo, una ciudad, \"ya te "
    "los pasé\", \"el segundo\") es on_topic aunque sola no diga de qué trata. En duda, on_topic: marca fuera de "
    "tema solo lo que claramente cae en los casos de NO on_topic."
)
CONTEXT_CHARS = 600  # cola del mensaje del agente: la pregunta suele ir al final


def _message_text(item: Any, role: str, types: tuple[str, ...]) -> str | None:
    """Texto de un item de mensaje con ese rol, o None si el item no es de ese rol o no trae texto."""
    if not isinstance(item, dict) or item.get("role") != role:
        return None
    content = item.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        texts = [c.get("text", "") for c in content if isinstance(c, dict) and c.get("type") in types]
        if texts:
            return "\n".join(texts)
    return None


def last_exchange(input_items: str | list[Any]) -> tuple[str, str]:
    """(ultimo mensaje del agente antes del ultimo del usuario, ultimo mensaje del usuario); "" si no hay."""
    if isinstance(input_items, str):
        return "", input_items
    for i in range(len(input_items) - 1, -1, -1):
        user = _message_text(input_items[i], "user", ("input_text", "text"))
        if user is None:
            continue
        for prev in reversed(input_items[:i]):
            agent = _message_text(prev, "assistant", ("output_text", "text"))
            if agent is not None:
                return agent, user
        return "", user
    return "", ""


def last_user_text(input_items: str | list[Any]) -> str:
    """Texto del ultimo mensaje del usuario en la entrada del agente (str o lista de items)."""
    return last_exchange(input_items)[1]


def guard_input(agent_text: str, user_text: str) -> str:
    """Lo que clasifica el guardia: el mensaje del usuario, con el ultimo del agente como contexto si hay."""
    user_text = user_text[:1000]
    agent_text = agent_text.strip()
    if not agent_text:
        return user_text
    return (
        f"Último mensaje del agente (contexto, no se clasifica):\n{agent_text[-CONTEXT_CHARS:]}\n\n"
        f"Mensaje del usuario a clasificar:\n{user_text}"
    )


def build_topic_guardrail(name: str, instructions: str, model: Model, log: logging.Logger, max_tokens: int = 80) -> InputGuardrail[Any]:
    guard_agent = Agent[Any](
        name=name,
        instructions=f"{instructions}\n\n{CONTEXT_RULES}",
        output_type=TopicVerdict,
        model=model,
        # sin razonamiento: gpt-6-luna razona "medium" por defecto y se comeria los 80 tokens (veredicto
        # cortado -> el guardia falla y deja pasar); gpt-5.4-nano tambien acepta "none"
        model_settings=ModelSettings(max_tokens=max_tokens, reasoning=Reasoning(effort="none")),
    )

    @input_guardrail(run_in_parallel=False)
    async def tema_guardrail(ctx: RunContextWrapper[Any], agent: Agent[Any], input_items: str | list[Any]) -> GuardrailFunctionOutput:
        agent_text, text = last_exchange(input_items)
        text = text.strip()
        if not text or len(text) < 3:
            return GuardrailFunctionOutput(output_info=None, tripwire_triggered=False)
        try:
            result = await Runner.run(guard_agent, guard_input(agent_text, text), context=ctx.context)
            verdict = result.final_output_as(TopicVerdict)
        except Exception as e:  # noqa: BLE001 - si el guardia falla, no se bloquea al usuario
            log.warning("guardrail fallo: %s", e)
            return GuardrailFunctionOutput(output_info=None, tripwire_triggered=False)
        if not verdict.on_topic:
            # sin el texto del usuario (puede traer telefono o correo); el motivo basta para revisar falsos positivos
            thread = getattr(ctx.context, "thread", None)
            log.info("guardrail bloqueo en %s: %s", getattr(thread, "id", "?"), verdict.reason)
        return GuardrailFunctionOutput(output_info=verdict, tripwire_triggered=not verdict.on_topic)

    return tema_guardrail
