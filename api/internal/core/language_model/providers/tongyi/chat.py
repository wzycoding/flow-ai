#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2026/5/15 
@Author : wzy
@File   : chat
"""
import os
from typing import Tuple

import tiktoken
from langchain_openai.chat_models.base import BaseChatOpenAI

from internal.core.language_model.entities.model_entity import BaseLanguageModel


class Chat(BaseChatOpenAI, BaseLanguageModel):
    """千问大语言模型基类"""

    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            openai_api_key=os.getenv("DASHSCOPE_API_KEY"),
            openai_api_base=os.getenv("DASHSCOPE_API_BASE"),
            **kwargs
        )

    def _get_encoding_model(self) -> Tuple[str, tiktoken.Encoding]:
        """重写获取编码模型名字+模型函数，该类继承OpenAI，词表模型可以使用gpt-3.5-turbo防止出错"""
        # 1.将DeepSeek的词表模型设置为gpt-3.5-turbo
        model = "gpt-3.5-turbo"

        # 2.返回模型名字+编码器
        return model, tiktoken.encoding_for_model(model)
