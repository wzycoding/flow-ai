#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pytest

from internal.core.workflow.nodes.code.code_node import CodeNode
from internal.exception import FailException


def test_execute_function_preserves_node_validation_error():
    with pytest.raises(FailException, match="代码中不能包含其他函数，只能有main函数"):
        CodeNode._execute_function("def helper(params):\n    return params", params={})


def test_execute_function_reports_syntax_error_line():
    with pytest.raises(FailException) as exc_info:
        CodeNode._execute_function("  def main(params):\n    return params", params={})

    assert exc_info.value.message == "Python代码语法错误（第1行）：unexpected indent"


def test_execute_function_reports_runtime_error():
    code = "def main(params):\n    return 1 / 0"

    with pytest.raises(FailException) as exc_info:
        CodeNode._execute_function(code, params={})

    assert exc_info.value.message == "Python代码执行出错：ZeroDivisionError: division by zero"


def test_fail_exception_string_contains_message():
    error = FailException("测试错误")

    assert str(error) == "测试错误"
