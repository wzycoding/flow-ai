#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/9/2
@Author : wzy
@File   : logging_extension
"""
import logging
import os.path

import structlog
from rich.console import Console
from rich.traceback import Traceback as RichTraceback
from concurrent_log_handler import ConcurrentTimedRotatingFileHandler
from flask import Flask


def _rich_traceback(sio, exc_info):
    """自定义 rich traceback：保留局部变量但限制帧数，避免输出过长"""
    sio.write("\n")
    traceback = RichTraceback.from_exception(
        *exc_info,
        show_locals=True,
        max_frames=6,
    )
    Console(file=sio, color_system=None).print(traceback)


def _reorder_keys(logger, method_name, event_dict):
    """将 request_id 等关键字段挪到日志输出最前面，便于快速识别请求链路"""
    priority_keys = ["request_id", "task_name"]
    ordered = {k: event_dict[k] for k in priority_keys if k in event_dict}
    ordered.update(event_dict)
    return ordered


def init_app(app: Flask):
    """日志记录器初始化，基于 structlog 实现结构化日志 + 链路追踪"""
    is_dev = app.debug or os.getenv("FLASK_ENV") == "development"

    # 1.配置 structlog 处理器链
    shared_processors = [
        structlog.contextvars.merge_contextvars,    # 自动注入 contextvars 中的 request_id 等上下文变量
        structlog.stdlib.add_logger_name,            # 注入 logger 名称（模块名）
        structlog.stdlib.add_log_level,              # 注入日志级别
        structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S", utc=False),  # 本地时间格式
        structlog.processors.StackInfoRenderer(),    # stack_info 支持
        structlog.processors.UnicodeDecoder(),       # 确保 UTF-8 编码
    ]

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,  # 桥接 stdlib logging
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),       # 使用 stdlib logger 作为底层
        wrapper_class=structlog.stdlib.BoundLogger,            # 兼容 stdlib 接口
        cache_logger_on_first_use=True,                        # 缓存 logger 实例提升性能
    )

    # 2.根据环境选择输出格式：开发用彩色文本，生产用 JSON
    if is_dev:
        formatter = structlog.stdlib.ProcessorFormatter(
            processors=[
                structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                _reorder_keys,                                      # request_id 显示在最前面
                structlog.dev.ConsoleRenderer(sort_keys=False, exception_formatter=_rich_traceback),
            ],
        )
    else:
        formatter = structlog.stdlib.ProcessorFormatter(
            processors=[
                structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                _reorder_keys,                                      # request_id 显示在最前面
                structlog.processors.JSONRenderer(ensure_ascii=False),
            ],
        )

    # 3.配置日志文件 handler（保留现有的按天轮转策略）
    log_folder = os.path.join(os.getcwd(), "storage", "log")
    if not os.path.exists(log_folder):
        os.makedirs(log_folder)

    log_file = os.path.join(log_folder, "app.log")
    file_handler = ConcurrentTimedRotatingFileHandler(
        log_file,
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)

    # 4.配置根 logger：统一设为 INFO，屏蔽第三方库（SQLAlchemy/werkzeug/urllib3等）的 DEBUG 噪音
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(file_handler)
    root.setLevel(logging.INFO)

    # 5.项目自身模块单独设为 DEBUG（通过 LOG_LEVEL 环境变量可覆盖，如 LOG_LEVEL=WARNING）
    app_log_level = getattr(logging, os.getenv("LOG_LEVEL", "DEBUG").upper(), logging.DEBUG)
    for module in ["internal", "pkg"]:
        logging.getLogger(module).setLevel(app_log_level)

    # 6.开发环境下同时将日志输出到控制台
    if is_dev:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.DEBUG)
        root.addHandler(console_handler)
