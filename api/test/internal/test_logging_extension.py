#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
from io import StringIO

from internal.extension.logging_extension import _rich_traceback


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
