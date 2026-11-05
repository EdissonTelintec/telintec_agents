# -*- coding: utf-8 -*-
"""Un turno completo sin streaming, para los canales de mensajeria (Telegram, despues WhatsApp...).

Mismo Store, mismos topes, mismo agente y misma contabilidad que el servidor de ChatKit; la
diferencia es que aqui la respuesta se devuelve entera como texto y el canal la manda.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import datetime

from agents import Agent, Runner
from agents.exceptions import InputGuardrailTripwireTriggered
from chatkit.agents import AgentContext, simple_to_agent_input
from chatkit.types import (
    AssistantMessageContent,
    AssistantMessageItem,
    InferenceOptions,
    ThreadMetadata,
    UserMessageItem,
    UserMessageTextContent,
)

from agents_service.context import RequestContext
from agents_service.limits import Limits
from agents_service.store import MySQLStore

log = logging.getLogger("agents.turn")


async def run_turn(
    store: MySQLStore,
    limits: Limits,
    agent: Agent[AgentContext],
    thread: ThreadMetadata,
    context: RequestContext,
    text: str,
    fixed_text: Callable[[str], str],
    history_limit: int = 40,
    max_turns: int = 6,
) -> str:
    """Guarda el mensaje del usuario, corre el agente y guarda la respuesta. Devuelve el texto."""
    user_item = UserMessageItem(
        id=store.generate_item_id("message", thread, context),
        thread_id=thread.id,
        created_at=datetime.now(),
        content=[UserMessageTextContent(text=text)],
        attachments=[],
        inference_options=InferenceOptions(),
    )
    await store.add_thread_item(thread.id, user_item, context)

    user_messages = await store.count_items(thread.id, "user_message")
    check = await limits.check(context, thread.id, is_new_conversation=user_messages <= 1)
    if not check.ok:
        log.info("tope %s en %s", check.reason, thread.id)
        reply = fixed_text("limit")
    else:
        page = await store.load_thread_items(thread.id, after=None, limit=history_limit, order="desc", context=context)
        agent_input = await simple_to_agent_input(list(reversed(page.data)))
        agent_context = AgentContext(thread=thread, store=store, request_context=context)
        try:
            result = await Runner.run(agent, agent_input, context=agent_context, max_turns=max_turns)
            reply = str(result.final_output or "").strip() or fixed_text("error")
            usage = result.context_wrapper.usage
            await limits.record_usage(context.agent, thread.id, usage.input_tokens, usage.output_tokens)
        except InputGuardrailTripwireTriggered:
            reply = fixed_text("off_topic")
        except Exception as e:  # noqa: BLE001 - el visitante recibe un texto, el detalle va al log
            log.exception("fallo el agente en %s: %s", thread.id, e)
            reply = fixed_text("error")

    assistant_item = AssistantMessageItem(
        id=store.generate_item_id("message", thread, context),
        thread_id=thread.id,
        created_at=datetime.now(),
        content=[AssistantMessageContent(text=reply)],
    )
    await store.add_thread_item(thread.id, assistant_item, context)
    return reply
