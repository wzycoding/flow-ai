#!/usr/bin/env python
# -*- coding: utf-8 -*-
from types import SimpleNamespace

import pytest
from langchain_core.documents import Document

from internal.service.vector_database_service import VectorDatabaseService


class DummyVectorStore:
    def __init__(self):
        self.documents = None
        self.kwargs = None

    def add_documents(self, documents, **kwargs):
        self.documents = documents
        self.kwargs = kwargs
        return kwargs.get("ids", [])


class DummyVectorDatabaseService(VectorDatabaseService):
    def __init__(self, failed_objects=None):
        self.weaviate = SimpleNamespace(
            client=SimpleNamespace(
                batch=SimpleNamespace(failed_objects=failed_objects or []),
            )
        )
        self.embeddings_service = None
        self.dummy_vector_store = DummyVectorStore()

    @property
    def vector_store(self):
        return self.dummy_vector_store


def test_vector_database_service_uses_configured_collection_name(monkeypatch):
    monkeypatch.setenv("WEAVIATE_COLLECTION_NAME", "DatasetTextEmbedding3Large")

    service = DummyVectorDatabaseService()

    assert service.collection_name == "DatasetTextEmbedding3Large"


def test_vector_database_service_raises_when_batch_has_failed_objects():
    service = DummyVectorDatabaseService(
        failed_objects=[
            SimpleNamespace(
                original_uuid="node-1",
                message="new node has a vector with length 3072. Existing nodes have vectors with length 1536",
            )
        ]
    )

    with pytest.raises(RuntimeError, match="向量数据库写入失败"):
        service.add_documents([Document(page_content="hello")], ids=["node-1"])
