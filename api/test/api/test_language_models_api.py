#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pkg.response import HttpCode


def test_get_language_models(client):
    resp = client.get("/language-models")

    assert resp.status_code == 200
    assert resp.json["code"] == HttpCode.SUCCESS
    provider_names = {provider["name"] for provider in resp.json["data"]}
    assert {"openai", "deepseek"}.issubset(provider_names)


def test_get_openai_model_detail(client):
    resp = client.get("/language-models/openai/gpt-4o-mini")

    assert resp.status_code == 200
    assert resp.json["code"] == HttpCode.SUCCESS
    assert resp.json["data"]["model_name"] == "gpt-4o-mini"


def test_provider_classes_use_current_langchain_integrations():
    from langchain_community.chat_models.baidu_qianfan_endpoint import QianfanChatEndpoint
    from langchain_community.chat_models.tongyi import ChatTongyi
    from langchain_deepseek import ChatDeepSeek
    from langchain_ollama import ChatOllama
    from langchain_openai import ChatOpenAI, OpenAI

    from internal.core.language_model.providers.deepseek.chat import Chat as DeepSeekChat
    from internal.core.language_model.providers.ollama.chat import Chat as OllamaChat
    from internal.core.language_model.providers.openai.chat import Chat as OpenAIChat
    from internal.core.language_model.providers.openai.completion import Completion as OpenAICompletion
    from internal.core.language_model.providers.tongyi.chat import Chat as TongyiChat
    from internal.core.language_model.providers.wenxin.chat import Chat as WenxinChat

    assert issubclass(OpenAIChat, ChatOpenAI)
    assert issubclass(OpenAICompletion, OpenAI)
    assert issubclass(DeepSeekChat, ChatDeepSeek)
    assert issubclass(OllamaChat, ChatOllama)
    assert issubclass(TongyiChat, ChatTongyi)
    assert issubclass(WenxinChat, QianfanChatEndpoint)


def test_embeddings_service_uses_text_embedding_3_large(monkeypatch):
    from redis import Redis

    from internal.service.embeddings_service import EmbeddingsService

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_API_BASE", "https://onesapi.com/v1")
    monkeypatch.delenv("OPENAI_EMBEDDING_MODEL", raising=False)

    embeddings_service = EmbeddingsService(Redis(host="localhost", port=6379))

    assert embeddings_service.embeddings.model == "text-embedding-3-large"
    assert str(embeddings_service.embeddings.openai_api_base) == "https://onesapi.com/v1"
