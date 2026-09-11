#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2026/9/10
@Author : wzy
@File   : usage_entity
"""
from enum import Enum


class UsageSource(str, Enum):
    """LLM用量记录的调用来源，用于区分一次模型消耗归属于哪类执行入口"""
    APP = "app"  # 应用会话调用（含调试、web应用、开放api、微信等所有绑定到具体app的对话）
    ASSISTANT = "assistant"  # 辅助Agent调用，不归属具体应用
    WORKFLOW = "workflow"  # 工作流内的LLM节点调用
    SUMMARY = "summary"  # 会话摘要、标题生成等后台辅助链调用
