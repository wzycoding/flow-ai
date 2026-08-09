#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2026/4/29
@Author : wzy
@File   : app_task
"""
import structlog

from uuid import UUID

from celery import shared_task

logger = structlog.get_logger()


@shared_task
def auto_create_app(
        name: str,
        description: str,
        account_id: UUID,
) -> None:
    """根据传递的名称、描述、账号id创建一个Agent"""
    logger.info("auto_create_app_started", name=name, account_id=str(account_id))
    try:
        from app.http.module import injector
        from internal.service import AppService

        app_service = injector.get(AppService)
        app_service.auto_create_app(name, description, account_id)
        logger.info("auto_create_app_completed", account_id=str(account_id))
    except Exception:
        logger.exception("auto_create_app_failed", account_id=str(account_id))
        raise
