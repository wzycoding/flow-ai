#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2026/4/18 
@Author : wzy
@File   : base_node
"""
from abc import ABC

from langchain_core.runnables import RunnableSerializable

from internal.core.workflow.entities.node_entity import BaseNodeData


class BaseNode(RunnableSerializable, ABC):
    """工作流节点基类"""
    node_data: BaseNodeData
