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
