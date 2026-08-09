#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/5/6
@Author : wzy
@File   : document_task
"""
import structlog

from uuid import UUID

from celery import shared_task

logger = structlog.get_logger()


@shared_task
def build_documents(document_ids: list[UUID]) -> None:
    """根据传递的文档id列表，构建文档"""
    logger.info("build_documents_started", document_ids=[str(d) for d in document_ids])
    try:
        from app.http.module import injector
        from internal.service.indexing_service import IndexingService

        indexing_service = injector.get(IndexingService)
        indexing_service.build_documents(document_ids)
        logger.info("build_documents_completed", document_count=len(document_ids))
    except Exception:
        logger.exception("build_documents_failed", document_ids=[str(d) for d in document_ids])
        raise


@shared_task
def update_document_enabled(document_id: UUID) -> None:
    """根据传递的文档id修改文档的状态"""
    logger.info("update_document_enabled_started", document_id=str(document_id))
    try:
        from app.http.module import injector
        from internal.service.indexing_service import IndexingService

        indexing_service = injector.get(IndexingService)
        indexing_service.update_document_enabled(document_id)
        logger.info("update_document_enabled_completed", document_id=str(document_id))
    except Exception:
        logger.exception("update_document_enabled_failed", document_id=str(document_id))
        raise


@shared_task
def delete_document(dataset_id: UUID, document_id: UUID) -> None:
    """根据传递的文档id+知识库id清除文档记录"""
    logger.info("delete_document_started", dataset_id=str(dataset_id), document_id=str(document_id))
    try:
        from app.http.module import injector
        from internal.service.indexing_service import IndexingService

        indexing_service = injector.get(IndexingService)
        indexing_service.delete_document(dataset_id, document_id)
        logger.info("delete_document_completed", dataset_id=str(dataset_id), document_id=str(document_id))
    except Exception:
        logger.exception("delete_document_failed", dataset_id=str(dataset_id), document_id=str(document_id))
        raise
