#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/6/30 00:07
@Author  : wzy
@File    : http.py
"""
import logging
import os
import time
import uuid

import structlog
from flask import Flask, request, g
from flask_cors import CORS
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_weaviate import FlaskWeaviate
from structlog.contextvars import bind_contextvars, clear_contextvars

from config import Config
from internal.cli import register_cli
from internal.exception import CustomException
from internal.extension import logging_extension, redis_extension, celery_extension
from internal.middleware import Middleware
from internal.router import Router
from pkg.response import json, Response, HttpCode
from pkg.sqlalchemy import SQLAlchemy


class Http(Flask):
    """Http服务引擎"""

    def __init__(
            self,
            *args,
            conf: Config,
            db: SQLAlchemy,
            weaviate: FlaskWeaviate,
            migrate: Migrate,
            login_manager: LoginManager,
            # 中间件
            middleware: Middleware,
            router: Router,
            **kwargs,
    ):
        # 1.调用父类构造函数初始化
        super().__init__(*args, **kwargs)

        # 2.初始化应用配置
        self.config.from_object(conf)

        # 3.注册绑定异常错误处理
        self.register_error_handler(Exception, self._register_error_handler)

        # 4.初始化flask扩展
        db.init_app(self)
        weaviate.init_app(self)
        migrate.init_app(self, db, directory="internal/migration")
        redis_extension.init_app(self)
        celery_extension.init_app(self)
        logging_extension.init_app(self)
        login_manager.init_app(self)

        # 5.解决前后端跨域问题
        CORS(self, resources={
            r"/*": {
                "origins": "*",
                "supports_credentials": True,
                # "methods": ["GET", "POST"],
                # "allow_headers": ["Content-Type"],
            }
        })

        # 6.注册应用中间件
        login_manager.request_loader(middleware.request_loader)

        # 7.注册应用路由
        router.register_router(self)

        # 8.注册请求生命周期钩子
        self._register_request_hooks()

        # 9.注册内部CLI命令
        register_cli(self)

    def _register_request_hooks(self):
        """注册请求生命周期钩子，实现请求链路追踪"""
        logger = structlog.get_logger()

        @self.before_request
        def _before_request():
            # 生成请求ID：优先使用客户端传入的，否则自动生成
            request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())[:8]
            clear_contextvars()
            bind_contextvars(request_id=request_id)
            g.request_id = request_id
            g.start_time = time.time()
            logger.info(
                "request_started",
                method=request.method,
                path=request.path,
                blueprint=request.blueprint,
            )

        @self.after_request
        def _after_request(response):
            latency = round(time.time() - g.get("start_time", time.time()), 3)
            logger.info(
                "request_completed",
                method=request.method,
                path=request.path,
                status=response.status_code,
                latency=latency,
            )
            # 在响应头中返回 request_id，方便前端反馈问题时定位
            response.headers["X-Request-ID"] = g.get("request_id", "")
            return response

    def _register_error_handler(self, error: Exception):
        logger = structlog.get_logger()

        # 1.业务异常：记录 warning 日志并返回结构化响应
        if isinstance(error, CustomException):
            logger.warning(
                "business_exception",
                exception_type=error.__class__.__name__,
                code=error.code.value if error.code else None,
                message=error.message,
                path=request.path,
                method=request.method,
            )
            return json(Response(
                code=error.code,
                message=error.message,
                data=error.data if error.data is not None else {},
            ))

        # 2.非预期异常：记录 error 日志（含完整堆栈）
        logger.error("unhandled_exception", error=str(error), exc_info=True)

        # 3.开发环境重新抛出异常便于调试，生产环境返回通用错误信息
        if self.debug or os.getenv("FLASK_ENV") == "development":
            raise error
        else:
            return json(Response(
                code=HttpCode.FAIL,
                message="服务器内部错误",
                data={},
            ))
