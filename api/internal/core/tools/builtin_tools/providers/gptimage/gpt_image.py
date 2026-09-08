#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2026/9/8
@Author : wzy
@File   : gpt-image
"""
import os
from typing import Any

import requests
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool

from internal.lib.helper import add_attribute


class GptImageArgsSchema(BaseModel):
    query: str = Field(description="输入生成图像的文本提示(prompt)")


class GptImageGenerationTool(BaseTool):
    """根据传入的提示词调用 gpt-image 模型生成图片"""
    name: str = "gpt_image"
    description: str = "当你想根据文本提示词生成图片时可以使用该工具，输入图像内容的描述，返回生成图片的URL地址"
    args_schema: type[BaseModel] = GptImageArgsSchema

    # 生成参数，来自工具配置（yaml params）
    size: str = "1024x1024"
    quality: str = "standard"
    style: str = "vivid"
    n: int = 1
    response_format: str = "url"

    def _run(self, *args: Any, **kwargs: Any) -> str:
        """根据提示词请求 gpt-image-2 接口生成图片，返回图片URL"""
        try:
            # 1.获取 gpt-image-2 服务配置，未配置则抛出错误
            base_url = os.getenv("GPT_IMAGE_URL", "").rstrip("/")
            api_key = os.getenv("GPT_IMAGE_KEY")
            if not base_url or not api_key:
                return "gpt-image服务未配置，请检查环境变量 GPT_IMAGE_URL / GPT_IMAGE_KEY"

            # 2.发起图片生成请求
            query = kwargs.get("query", "") or (args[0] if args else "")
            response = requests.post(
                url=f"{base_url}/images/generations",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "gpt-image-2",
                    "prompt": query,
                    "size": self.size,
                    "quality": self.quality,
                    "style": self.style,
                    "n": int(self.n),
                    "response_format": self.response_format,
                },
                timeout=180,
            )
            response.raise_for_status()
            data = response.json()

            # 3.提取生成结果，url 模式返回图片链接，b64_json 模式返回编码数据
            results = []
            for item in data.get("data", []):
                if item.get("url"):
                    results.append(item["url"])
                elif item.get("b64_json"):
                    results.append(item["b64_json"])
            if not results:
                return f"生成图片失败: {data.get('error') or data}"
            return "\n".join(results)
        except Exception as e:
            return f"生成图片失败: {str(e)}"


@add_attribute("args_schema", GptImageArgsSchema)
def gpt_image(**kwargs) -> BaseTool:
    """返回gpt-image的LangChain工具"""
    return GptImageGenerationTool(**kwargs)
