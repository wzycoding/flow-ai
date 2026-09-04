#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import re
import sys
from io import StringIO
from types import SimpleNamespace

from internal.extension.logging_extension import _rich_traceback, init_app


def test_rich_traceback_renders_exception():
    try:
        raise ValueError("测试日志异常")
    except ValueError:
        exc_info = sys.exc_info()

    output = StringIO()
    _rich_traceback(output, exc_info)

    rendered = output.getvalue()
    assert "ValueError" in rendered
    assert "测试日志异常" in rendered


def test_rich_traceback_does_not_render_frame_locals():
    secret_value = "-".join(("should", "not", "be", "printed"))
    try:
        raise ValueError("测试日志异常")
    except ValueError:
        exc_info = sys.exc_info()

    output = StringIO()
    _rich_traceback(output, exc_info)

    rendered = output.getvalue()
    assert "ValueError" in rendered
    assert "测试日志异常" in rendered
    assert secret_value not in rendered


def test_stdlib_logs_include_timestamp(monkeypatch, tmp_path, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("FLASK_ENV", "development")

    root = logging.getLogger()
    previous_handlers = root.handlers[:]
    previous_level = root.level
    try:
        init_app(SimpleNamespace(debug=True))
        logging.getLogger("internal.logging_test").info("普通日志")

        rendered = capsys.readouterr().err
    finally:
        for handler in root.handlers:
            handler.close()
        root.handlers[:] = previous_handlers
        root.setLevel(previous_level)

    assert re.search(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", rendered)
    assert "普通日志" in rendered


def test_production_logs_render_traceback_as_text(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("FLASK_ENV", "production")

    root = logging.getLogger()
    previous_handlers = root.handlers[:]
    previous_level = root.level
    try:
        init_app(SimpleNamespace(debug=False))
        try:
            raise ValueError("生产环境异常")
        except ValueError:
            logging.getLogger("internal.logging_test").error("异常日志", exc_info=True)

        rendered = (tmp_path / "storage" / "log" / "app.log").read_text()
    finally:
        for handler in root.handlers:
            handler.close()
        root.handlers[:] = previous_handlers
        root.setLevel(previous_level)

    assert '"exception": "Traceback (most recent call last):' in rendered
    assert '"exc_info"' not in rendered
    assert "生产环境异常" in rendered
