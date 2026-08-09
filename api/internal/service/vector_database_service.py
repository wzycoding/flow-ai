#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/2/27 
@Author : wzy
@File   : vector_database_service
"""
import os
from dataclasses import dataclass
from typing import Any

from flask import Flask
from flask_weaviate import FlaskWeaviate
from injector import inject
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_weaviate import WeaviateVectorStore
from weaviate.collections import Collection

from .embeddings_service import EmbeddingsService

# 向量数据库的默认集合名字
COLLECTION_NAME = "Dataset"


@inject
@dataclass
class VectorDatabaseService:
    """向量数据库服务"""
    weaviate: FlaskWeaviate
    embeddings_service: EmbeddingsService

    @property
    def collection_name(self) -> str:
        return os.getenv("WEAVIATE_COLLECTION_NAME", COLLECTION_NAME)

    async def _get_client(self, flask_app: Flask):
        with flask_app.app_context():
            return self.weaviate.client

    @property
    def vector_store(self) -> WeaviateVectorStore:
        return WeaviateVectorStore(
            client=self.weaviate.client,
            index_name=self.collection_name,
            text_key="text",
            embedding=self.embeddings_service.cache_backed_embeddings,
        )

    def add_documents(self, documents: list[Document], **kwargs: Any) -> list[str]:
        """往向量数据库中新增文档，并将 Weaviate batch 失败转成业务异常。"""
        ids = self.vector_store.add_documents(documents, **kwargs)
        failed_objects = getattr(self.weaviate.client.batch, "failed_objects", []) or []
        if failed_objects:
            errors = []
            for failed_object in failed_objects:
                original_uuid = getattr(failed_object, "original_uuid", "")
                message = getattr(failed_object, "message", str(failed_object))
                errors.append(f"{original_uuid}: {message}" if original_uuid else message)
            raise RuntimeError("向量数据库写入失败: " + "; ".join(errors))
        return ids

    def get_retriever(self) -> VectorStoreRetriever:
        """获取检索器"""
        return self.vector_store.as_retriever()

    @property
    def collection(self) -> Collection:
        return self.weaviate.client.collections.get(self.collection_name)
