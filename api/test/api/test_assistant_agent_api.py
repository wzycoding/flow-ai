#!/usr/bin/env python
# -*- coding: utf-8 -*-

from internal.service.assistant_agent_service import AssistantAgentService
from internal.core.agent.entities.queue_entity import QueueEvent, queue_event_name


class FakeLanguageModelService:
    def __init__(self):
        self.config = None
        self.llm = object()

    def load_language_model(self, model_config):
        self.config = model_config
        return self.llm


def test_assistant_agent_llm_uses_env_model_config(monkeypatch):
    fake_language_model_service = FakeLanguageModelService()
    service = AssistantAgentService(
        db=None,
        conversation_service=None,
        language_model_service=fake_language_model_service,
    )

    monkeypatch.setenv("ASSISTANT_AGENT_MODEL_PROVIDER", "openai")
    monkeypatch.setenv("ASSISTANT_AGENT_MODEL", "gpt-4o-mini")
    monkeypatch.setenv("ASSISTANT_AGENT_TEMPERATURE", "0.2")
    monkeypatch.setenv("ASSISTANT_AGENT_MAX_TOKENS", "512")

    llm = service.load_assistant_agent_llm()

    assert llm is fake_language_model_service.llm
    assert fake_language_model_service.config == {
        "provider": "openai",
        "model": "gpt-4o-mini",
        "parameters": {
            "temperature": 0.2,
            "max_tokens": 512,
        },
    }


def test_queue_event_name_uses_sse_protocol_value():
    assert str(QueueEvent.AGENT_MESSAGE) == "QueueEvent.AGENT_MESSAGE"
    assert queue_event_name(QueueEvent.AGENT_MESSAGE) == "agent_message"
