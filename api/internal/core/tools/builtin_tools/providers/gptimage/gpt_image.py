#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2026/9/8
@Author : wzy
@File   : gpt-image
"""
import os
import uuid
from datetime import datetime
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

            # 2.发起图片生成请求，上游网关偶发SSL中断，失败重试一次
            query = kwargs.get("query", "") or (args[0] if args else "")
            for attempt in range(2):
                try:
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
                    break
                except (requests.ConnectionError, requests.Timeout):
                    if attempt >= 1:
                        raise
            data = response.json()
            if response.status_code != 200:
                error = data.get("error")
                if isinstance(error, dict):
                    error = error.get("message") or error
                return f"生成图片失败({response.status_code}): {error or response.text[:200]}"

            # 3.提取生成结果并转存到腾讯云COS，返回COS地址
            from internal.service import CosService
            from app.http.module import injector

            cos_service = injector.get(CosService)
            client = cos_service.get_client()
            bucket = cos_service.get_bucket()
            now = datetime.now()

            results = []
            for item in data.get("data", []):
                image_url = item.get("url")
                if not image_url:
                    continue
                # 4.下载上游生成的图片并上传到COS存储
                image_content = requests.get(image_url, timeout=60).content
                key = (
                    f"builtin-tools/gpt-image/{now.year}/{now.month:02d}/{now.day:02d}/"
                    f"{uuid.uuid4()}.png"
                )
                client.put_object(Bucket=bucket, Key=key, Body=image_content)
                results.append(CosService.get_file_url(key))
            if not results:
                error = data.get("error")
                if isinstance(error, dict):
                    error = error.get("message") or error
                return f"生成图片失败: {error or data}"
            return "\n".join(results)
        except Exception as e:
            return f"生成图片失败: {str(e)}"


@add_attribute("args_schema", GptImageArgsSchema)
def gpt_image(**kwargs) -> BaseTool:
    """返回gpt-image的LangChain工具"""
    return GptImageGenerationTool(**kwargs)
