#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/3/3 
@Author : wzy
@File   : tool_entity
"""
from enum import Enum
from typing import Optional, Any

from pydantic import BaseModel, Field


class ToolParamType(str, Enum):
    """工具参数类型枚举类"""
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    SELECT = "select"


class ToolParam(BaseModel):
    """工具参数类型"""
    name: str  # 参数实际名字
    label: str  # 参数展示类型
    type: ToolParamType  # 参数类型
    required: bool = False  # 是否必填
    default: Optional[Any] = None  # 默认值
    min: Optional[float] = None  # 最小值
    max: Optional[float] = None  # 最大值
    options: list[dict[str, Any]] = Field(default_factory=list)  # 下拉菜单选项列表


class ToolEntity(BaseModel):
    """工具实体类，存储的信息映射的是工具名.yaml里面的数据"""
    name: str
    label: str
    description: str
    params: list[ToolParam] = Field(default_factory=list)
