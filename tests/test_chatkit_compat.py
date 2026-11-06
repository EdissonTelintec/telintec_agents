# -*- coding: utf-8 -*-
"""Citas de File Search en el stream de ChatKit (sin red).

`openai` 3.46 trae para `response.output_text.annotation.added` sus propias clases de anotacion y
`openai-chatkit` 1.6.5 valida contra las de `response_output_text`: sin el parche de `agents_service.chat`
el turno truena en cuanto el asistente cita una guia del vector store.
"""

from __future__ import annotations

import chatkit.agents as chatkit_agents
import pytest
from chatkit.agents import ResponseStreamConverter
from chatkit.types import FileSource
from openai.types.responses.response_output_text_annotation_added_event import AnnotationFileCitation as EventFileCitation
from pydantic import ValidationError

from agents_service import chat
from agents_service.agents.assistant import GuideCitationConverter
from agents_service.knowledge import HelpBase

CITATION = EventFileCitation(file_id="file-abc", filename="almacen.md", index=42, type="file_citation")


async def test_guide_citation_shows_guide_title():
    converter = GuideCitationConverter(HelpBase.load())
    annotation = await chatkit_agents._convert_annotation(CITATION, converter)
    assert annotation is not None and annotation.index == 42
    assert isinstance(annotation.source, FileSource)
    assert annotation.source.title == "Almacén" and annotation.source.filename == "almacen.md"
    other = EventFileCitation(file_id="file-x", filename="otro.md", index=0, type="file_citation")
    unknown = await chatkit_agents._convert_annotation(other, converter)
    assert unknown is not None and unknown.source.title == "otro.md"


async def test_event_file_citation_becomes_annotation():
    annotation = await chatkit_agents._convert_annotation(CITATION, ResponseStreamConverter())
    assert annotation is not None
    assert annotation.index == 42
    assert isinstance(annotation.source, FileSource) and annotation.source.filename == "almacen.md"


async def test_upstream_still_rejects_event_citation():
    """Si esto deja de fallar al actualizar chatkit/openai, el parche de `chat.py` ya no hace falta."""
    with pytest.raises(ValidationError):
        await chat._convert_annotation_upstream(CITATION, ResponseStreamConverter())
