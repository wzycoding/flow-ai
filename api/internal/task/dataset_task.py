#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/11/8
@Author : wzy
@File   : dataset_task
"""
import structlog

from uuid import UUID

from celery import shared_task

logger = structlog.get_logger()


@shared_task
def delete_dataset(dataset_id: UUID) -> None:
    """根据传递的知识库id删除特定的知识库信息"""
    logger.info("delete_dataset_started", dataset_id=str(dataset_id))
    try:
        from app.http.module import injector
        from internal.service import IndexingService

        indexing_service = injector.get(IndexingService)
        indexing_service.delete_dataset(dataset_id)
        logger.info("delete_dataset_completed", dataset_id=str(dataset_id))
    except Exception:
        logger.exception("delete_dataset_failed", dataset_id=str(dataset_id))
        raise
