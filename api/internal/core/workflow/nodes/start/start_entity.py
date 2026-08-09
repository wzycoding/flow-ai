#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2026/4/18 
@Author : wzy
@File   : start_entity
"""
from pydantic import Field

from internal.core.workflow.entities.node_entity import BaseNodeData
from internal.core.workflow.entities.variable_entity import VariableEntity


class StartNodeData(BaseNodeData):
    """开始节点数据"""
    inputs: list[VariableEntity] = Field(default_factory=list)  # 开始节点的输入变量信息
