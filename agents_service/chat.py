# -*- coding: utf-8 -*-
"""Servidor de ChatKit comun a los agentes: topes, historial, corrida del agente y contabilidad.

`respond()` se llama por cada mensaje nuevo del usuario (ya guardado en el Store). Carga los ultimos
items de la conversacion, los convierte a entrada del Agents SDK y transmite la respuesta con
`stream_agent_response`; el servidor de ChatKit persiste cada `ThreadItemDoneEvent`.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator, Callable
from datetime import datetime

import chatkit.agents as _chatkit_agents
from agents import Agent, Runner
from agents.exceptions import InputGuardrailTripwireTriggered
from chatkit.agents import AgentContext, ResponseStreamConverter, simple_to_agent_input, stream_agent_response
from chatkit.server import ChatKitServer
from chatkit.types import Annotation, AssistantMessageContent, AssistantMessageItem, ThreadItemDoneEvent, ThreadMetadata, ThreadStreamEvent, UserMessageItem
from pydantic import BaseModel

from agents_service.config import Settings
from agents_service.context import RequestContext
from agents_service.limits import Limits
from agents_service.store import MySQLStore

log = logging.getLogger("agents.chat")

# openai 3.46 trae para `response.output_text.annotation.added` sus propias clases de anotacion y
# openai-chatkit 1.6.5 valida contra las de `response_output_text` (mismos campos): pydantic rechaza la
# instancia y el turno truena en cuanto File Search cita una guia. Como dict, chatkit la reconstruye.
# tests/test_chatkit_compat.py avisa cuando el parche ya no haga falta.
_convert_annotation_upstream = _chatkit_agents._convert_annotation


async def _convert_annotation(raw_annotation: object, converter: ResponseStreamConverter) -> Annotation | None:
    if isinstance(raw_annotation, BaseModel):
        raw_annotation = raw_annotation.model_dump()
    return await _convert_annotation_upstream(raw_annotation, converter)


_chatkit_agents._convert_annotation = _convert_annotation

AgentFactory = Callable[[RequestContext], Agent[AgentContext]]
TextProvider = Callable[[str], str]  # kind -> texto fijo ("limit", "off_topic", "error")


class TelintecChatKitServer(ChatKitServer[RequestContext]):
    def __init__(
        self,
        store: MySQLStore,
        settings: Settings,
        limits: Limits,
        agent_factory: AgentFactory,
        fixed_text: TextProvider,
        allowed_image_domains: list[str] | None = None,
        history_limit: int = 40,
        max_turns: int = 6,
        converter: ResponseStreamConverter | None = None,  # p. ej. citas de File Search con titulo de guia
    ):
        super().__init__(store)
        self.mysql_store = store
        self.settings = settings
        self.limits = limits
        self.agent_factory = agent_factory
        self.fixed_text = fixed_text
        self.converter = converter or ResponseStreamConverter()
        self.allowed_image_domains = allowed_image_domains or []
        self.history_limit = history_limit
        self.max_turns = max_turns

    def _message(self, thread: ThreadMetadata, context: RequestContext, text: str) -> ThreadItemDoneEvent:
        item = AssistantMessageItem(
            id=self.store.generate_item_id("message", thread, context),
            thread_id=thread.id,
            created_at=datetime.now(),
            content=[AssistantMessageContent(text=text)],
        )
        return ThreadItemDoneEvent(item=item)

    async def respond(
        self, thread: ThreadMetadata, input_user_message: UserMessageItem | None, context: RequestContext
    ) -> AsyncIterator[ThreadStreamEvent]:
        if self.allowed_image_domains and not thread.allowed_image_domains:
            thread.allowed_image_domains = list(self.allowed_image_domains)
            await self.store.save_thread(thread, context)

        user_messages = await self.mysql_store.count_items(thread.id, "user_message")
        check = await self.limits.check(context, thread.id, is_new_conversation=user_messages <= 1)
        if not check.ok:
            log.info("tope %s en %s", check.reason, thread.id)
            yield self._message(thread, context, self.fixed_text("limit"))
            return

        page = await self.store.load_thread_items(thread.id, after=None, limit=self.history_limit, order="desc", context=context)
        items = list(reversed(page.data))
        agent_input = await simple_to_agent_input(items)
        agent_context = AgentContext(thread=thread, store=self.store, request_context=context)
        agent = self.agent_factory(context)
        result = Runner.run_streamed(agent, agent_input, context=agent_context, max_turns=self.max_turns)
        try:
            async for event in stream_agent_response(agent_context, result, converter=self.converter):
                yield event
        except InputGuardrailTripwireTriggered:
            yield self._message(thread, context, self.fixed_text("off_topic"))
        except Exception as e:  # noqa: BLE001 - el visitante recibe un texto, el detalle va al log
            log.exception("fallo el agente en %s: %s", thread.id, e)
            yield self._message(thread, context, self.fixed_text("error"))
        finally:
            usage = result.context_wrapper.usage
            try:
                await self.limits.record_usage(context.agent, thread.id, usage.input_tokens, usage.output_tokens)
            except Exception as e:  # noqa: BLE001
                log.warning("no se registro el consumo de %s: %s", thread.id, e)
