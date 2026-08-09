#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2026/6/22 
@Author : wzy
@File   : mcp_provider_manager
"""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any, Callable
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from injector import inject
from langchain_core.messages import ToolMessage
from langchain_core.tools import BaseTool, StructuredTool
from pydantic import BaseModel

from langchain_mcp_adapters.client import MultiServerMCPClient

from internal.core.tools.mcp_tools.entities import McpToolEntity


@inject
@dataclass
class McpProviderManager(BaseModel):
    """MCP工具提供者管理器，负责加载并包装Streamable HTTP MCP工具"""

    @classmethod
    def get_server_name(cls, provider_id: str) -> str:
        """获取传递给LangChain MCP适配器的server name"""
        return f"mcp_{provider_id}"

    @classmethod
    def build_connection(cls, url: str, headers: dict[str, str] | None = None) -> dict[str, Any]:
        """构建langchain-mcp-adapters需要的连接配置"""
        return {
            "transport": "http",
            "url": cls.normalize_url(url),
            "headers": headers or {},
        }

    @classmethod
    def normalize_url(cls, url: str) -> str:
        """规范化HTTP URL，清理query参数中常见的误输入空格"""
        parsed = urlparse(url.strip())
        query_pairs = [
            (key.strip(), value.strip())
            for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        ]
        return urlunparse(parsed._replace(query=urlencode(query_pairs)))

    @classmethod
    async def aload_tools(
            cls,
            server_name: str,
            connection: dict[str, Any],
            tool_name_prefix: bool = False,
    ) -> list[BaseTool]:
        """异步加载指定MCP服务器的工具列表"""
        client = MultiServerMCPClient(
            {server_name: connection},
            tool_name_prefix=tool_name_prefix,
        )
        return await client.get_tools(server_name=server_name)

    @classmethod
    def load_tools(
            cls,
            server_name: str,
            connection: dict[str, Any],
            tool_name_prefix: bool = False,
    ) -> list[BaseTool]:
        """同步加载指定MCP服务器的工具列表"""
        return cls._run_async(lambda: cls.aload_tools(server_name, connection, tool_name_prefix))

    @classmethod
    def invoke_loaded_tool(cls, tool: BaseTool, kwargs: dict[str, Any]) -> Any:
        """同步调用已加载的MCP工具，用于运行和凭证探测"""
        return cls._serialize_tool_result(cls._run_async(lambda: tool.ainvoke(kwargs)))

    @classmethod
    def get_tool(cls, tool_entity: McpToolEntity) -> BaseTool:
        """根据MCP工具实体信息获取一个同步可调用的LangChain工具"""
        server_name = cls.get_server_name(tool_entity.provider_id)
        connection = cls.build_connection(tool_entity.url, tool_entity.headers)
        tools = cls.load_tools(server_name, connection, tool_name_prefix=True)
        expected_tool_name = f"{server_name}_{tool_entity.name}"

        for tool in tools:
            if tool.name == expected_tool_name:
                return cls._wrap_async_tool(tool)

        raise ValueError("该MCP工具不存在或MCP服务器未返回对应工具")

    @classmethod
    def _wrap_async_tool(cls, tool: BaseTool) -> BaseTool:
        """将MCP适配器产出的异步工具包装成当前项目同步Agent/Workflow可调用的工具"""

        def sync_func(**kwargs: Any) -> Any:
            return cls.invoke_loaded_tool(tool, kwargs)

        return StructuredTool(
            name=tool.name,
            description=tool.description or "",
            args_schema=tool.args_schema,
            func=sync_func,
            metadata=tool.metadata,
        )

    @classmethod
    def _run_async(cls, coroutine_factory: Callable[[], Any]) -> Any:
        """在同步上下文安全运行异步MCP调用"""
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(coroutine_factory())

        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(lambda: asyncio.run(coroutine_factory()))
            return future.result()

    @classmethod
    def _serialize_tool_result(cls, value: Any) -> Any:
        """将MCP工具返回值转换为可JSON序列化的数据"""
        if isinstance(value, tuple) and len(value) == 2:
            content, artifact = value
            content = cls._serialize_tool_result(content)
            artifact = cls._serialize_tool_result(artifact)
            if artifact:
                return {"content": content, "artifact": artifact}
            return content

        if isinstance(value, ToolMessage):
            payload = {"content": cls._serialize_tool_result(value.content)}
            if value.artifact:
                payload["artifact"] = cls._serialize_tool_result(value.artifact)
            return payload

        if isinstance(value, BaseModel):
            return value.model_dump(mode="json")

        if isinstance(value, list):
            text_blocks = [
                item.get("text", "")
                for item in value
                if isinstance(item, dict) and item.get("type") == "text"
            ]
            if len(text_blocks) == len(value):
                return "\n".join(text_blocks)
            return [cls._serialize_tool_result(item) for item in value]

        if isinstance(value, dict):
            return {str(k): cls._serialize_tool_result(v) for k, v in value.items()}

        if isinstance(value, bytes):
            return value.decode("utf-8", errors="replace")

        return value
