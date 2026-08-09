#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/3/7 
@Author : wzy
@File   : current_time
"""
from datetime import datetime
from typing import Any

from pydantic import BaseModel
from langchain_core.tools import BaseTool


class CurrentTimeArgsSchema(BaseModel):
    """当前时间工具无输入参数。"""
    pass


class CurrentTimeTool(BaseTool):
    """一个用于获取当前时间的工具"""
    name: str = "current_time"
    description: str = "一个用于获取当前时间的工具"
    args_schema: type[BaseModel] = CurrentTimeArgsSchema

    def _run(self, *args: Any, **kwargs: Any) -> Any:
        """获取当前系统的时间并进行格式化后返回"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S %Z")


def current_time(**kwargs) -> BaseTool:
    """返回获取当前时间的LangChain工具"""
    return CurrentTimeTool()
