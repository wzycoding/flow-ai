#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2026/4/27
@Author : wzy
@File    : chat.py
"""
import os

from langchain_openai import ChatOpenAI

from internal.core.language_model.entities.model_entity import BaseLanguageModel


class Chat(ChatOpenAI, BaseLanguageModel):
    """OpenAI聊天模型基类"""

    def __init__(self, **kwargs):
        kwargs.setdefault("base_url", os.environ.get("OPENAI_API_BASE"))
        kwargs.setdefault("api_key", os.environ.get("OPENAI_API_KEY"))
        # 为tiktoken不认识的模型设置回退模型名，用于token计数
        if "tiktoken_model_name" not in kwargs:
            model = kwargs.get("model", "")
            if not model.startswith("gpt-3.5-turbo") and not model.startswith("gpt-4"):
                kwargs["tiktoken_model_name"] = "gpt-4o"
        super().__init__(**kwargs)
