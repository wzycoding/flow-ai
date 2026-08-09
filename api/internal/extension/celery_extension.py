#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/5/6 
@Author : wzy
@File   : celery_extension
"""
import structlog
from celery import Task, Celery
from celery.signals import task_prerun, task_postrun, task_failure
from flask import Flask
from structlog.contextvars import bind_contextvars, clear_contextvars


def init_app(app: Flask):
    """Celery配置服务初始化"""

    class FlaskTask(Task):
        """定义FlaskTask，确保Celery在Flask应用的上下文中运行，这样可以访问flask配置、数据库等内容"""

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    # 1.创建Celery应用并配置
    celery_app = Celery(app.name, task_cls=FlaskTask)
    celery_app.config_from_object(app.config["CELERY"])
    celery_app.set_default()

    # 2.将celery挂在到app的扩展中
    app.extensions["celery"] = celery_app

    # 3.注册Celery信号处理器，实现任务日志和 request_id 传递
    logger = structlog.get_logger()

    @task_prerun.connect
    def on_task_prerun(task_id, task, **kwargs):
        clear_contextvars()
        bind_contextvars(request_id=f"celery-{task_id[:8]}", task_name=task.name)
        logger.info("task_started", task_id=task_id)

    @task_postrun.connect
    def on_task_postrun(task_id, task, **kwargs):
        logger.info("task_completed", task_id=task_id)
        clear_contextvars()

    @task_failure.connect
    def on_task_failure(task_id, exception, **kwargs):
        logger.error("task_failed", task_id=task_id, error=str(exception), exc_info=True)
        clear_contextvars()
