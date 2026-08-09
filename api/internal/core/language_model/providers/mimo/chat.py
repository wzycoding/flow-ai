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
    """小米MiMo聊天模型基类"""

    def __init__(self, **kwargs):
        kwargs.setdefault("base_url", os.environ.get("MIMO_API_BASE"))
        kwargs.setdefault("api_key", os.environ.get("MIMO_API_KEY"))
        kwargs.setdefault("tiktoken_model_name", "gpt-4o")
        super().__init__(**kwargs)
