#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2026/6/22 
@Author : wzy
@File   : mcp_tool_service
"""
import json
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse
from uuid import UUID

from injector import inject
from langchain_core.tools import BaseTool
from pydantic import BaseModel
from sqlalchemy import desc

from internal.core.tools.mcp_tools.providers import McpProviderManager
from internal.exception import ValidateErrorException, NotFoundException
from internal.model import Account, McpToolProvider, McpTool
from internal.schema.mcp_tool_schema import (
    CreateMcpToolReq,
    GetMcpToolProvidersWithPageReq,
    UpdateMcpToolProviderReq,
)
from pkg.paginator import Paginator
from pkg.sqlalchemy import SQLAlchemy
from .base_service import BaseService


SUPPORTED_TRANSPORTS = {"http", "streamable_http", "streamable-http", "streamhttp"}
UNSUPPORTED_TRANSPORTS = {"stdio", "sse", "websocket"}


@inject
@dataclass
class McpToolService(BaseService):
    """MCP插件服务"""
    db: SQLAlchemy
    mcp_provider_manager: McpProviderManager

    def validate_mcp_schema(self, mcp_schema: str) -> list[dict[str, Any]]:
        """校验MCP配置并返回可用工具预览"""
        servers = self.parse_mcp_schema(mcp_schema)
        previews = []
        for server in servers:
            tools = self._load_remote_tools(server)
            previews.append({**server, "tools": tools})
        return previews

    def create_mcp_tools(self, req: CreateMcpToolReq, account: Account) -> None:
        """根据传递的请求批量创建MCP插件"""
        servers = self.parse_mcp_schema(req.mcp_schema.data)
        server_names = [server["name"] for server in servers]
        if len(server_names) != len(set(server_names)):
            raise ValidateErrorException("MCP服务器名称存在重复")

        exists_count = self.db.session.query(McpToolProvider).filter(
            McpToolProvider.account_id == account.id,
            McpToolProvider.name.in_(server_names),
        ).count()
        if exists_count:
            raise ValidateErrorException("当前账号下已存在同名MCP服务器")

        server_tools = []
        for server in servers:
            tools = self._load_remote_tools(server)
            server_tools.append((server, tools))

        with self.db.auto_commit():
            for server, tools in server_tools:
                provider = McpToolProvider(
                    account_id=account.id,
                    name=server["name"],
                    description=server["description"],
                    transport=server["config"]["transport"],
                    url=server["config"]["url"],
                    headers=server["config"]["headers"],
                    config=server["config"],
                    mcp_schema=server["mcp_schema"],
                )
                self.db.session.add(provider)
                self.db.session.flush()

                for tool in tools:
                    self.db.session.add(McpTool(
                        account_id=account.id,
                        provider_id=provider.id,
                        name=tool["name"],
                        description=tool["description"],
                        input_schema=tool["input_schema"],
                        tool_metadata=tool["metadata"],
                    ))

    def update_mcp_tool_provider(
            self,
            provider_id: UUID,
            req: UpdateMcpToolProviderReq,
            account: Account,
    ):
        """更新MCP工具提供者信息并重新同步工具列表"""
        provider = self.get_mcp_tool_provider(provider_id, account)
        servers = self.parse_mcp_schema(req.mcp_schema.data)
        if len(servers) != 1:
            raise ValidateErrorException("更新单个MCP服务器时只允许传递一个mcpServers配置")

        server = servers[0]
        check_provider = self.db.session.query(McpToolProvider).filter(
            McpToolProvider.account_id == account.id,
            McpToolProvider.name == server["name"],
            McpToolProvider.id != provider.id,
        ).one_or_none()
        if check_provider:
            raise ValidateErrorException("当前账号下已存在同名MCP服务器")

        tools = self._load_remote_tools(server)

        with self.db.auto_commit():
            self.db.session.query(McpTool).filter(
                McpTool.provider_id == provider.id,
                McpTool.account_id == account.id,
            ).delete()

            provider.name = server["name"]
            provider.description = server["description"]
            provider.transport = server["config"]["transport"]
            provider.url = server["config"]["url"]
            provider.headers = server["config"]["headers"]
            provider.config = server["config"]
            provider.mcp_schema = server["mcp_schema"]

            for tool in tools:
                self.db.session.add(McpTool(
                    account_id=account.id,
                    provider_id=provider.id,
                    name=tool["name"],
                    description=tool["description"],
                    input_schema=tool["input_schema"],
                    tool_metadata=tool["metadata"],
                ))

    def get_mcp_tool_providers_with_page(
            self,
            req: GetMcpToolProvidersWithPageReq,
            account: Account,
    ) -> tuple[list[Any], Paginator]:
        """获取MCP工具服务提供者分页列表数据"""
        paginator = Paginator(db=self.db, req=req)
        filters = [McpToolProvider.account_id == account.id]
        if req.search_word.data:
            filters.append(McpToolProvider.name.ilike(f"%{req.search_word.data}%"))

        providers = paginator.paginate(
            self.db.session.query(McpToolProvider).filter(*filters).order_by(desc("created_at"))
        )
        return providers, paginator

    def get_mcp_tool(self, provider_id: UUID, tool_name: str, account: Account) -> McpTool:
        """根据provider_id和tool_name获取MCP工具详情"""
        tool = self.db.session.query(McpTool).filter_by(
            provider_id=provider_id,
            name=tool_name,
        ).one_or_none()
        if tool is None or tool.account_id != account.id:
            raise NotFoundException("该MCP工具不存在")
        return tool

    def get_mcp_tool_provider(self, provider_id: UUID, account: Account) -> McpToolProvider:
        """根据provider_id获取MCP工具提供者"""
        provider = self.get(McpToolProvider, provider_id)
        if provider is None or provider.account_id != account.id:
            raise NotFoundException("该MCP工具提供者不存在")
        return provider

    def delete_mcp_tool_provider(self, provider_id: UUID, account: Account) -> None:
        """删除MCP工具提供者及其工具"""
        provider = self.get_mcp_tool_provider(provider_id, account)
        with self.db.auto_commit():
            self.db.session.query(McpTool).filter(
                McpTool.provider_id == provider_id,
                McpTool.account_id == account.id,
            ).delete()
            self.db.session.delete(provider)

    @classmethod
    def parse_mcp_schema(cls, mcp_schema_str: str) -> list[dict[str, Any]]:
        """解析并校验MCP JSON配置"""
        try:
            data = json.loads(mcp_schema_str.strip())
            if not isinstance(data, dict):
                raise ValueError("MCP schema must be a JSON object")
        except Exception:
            raise ValidateErrorException("传递数据必须是符合MCP配置规范的JSON字符串")

        servers = data.get("mcpServers")
        if not isinstance(servers, dict) or len(servers) <= 0:
            raise ValidateErrorException("MCP配置必须包含非空的mcpServers对象")

        normalized_servers = []
        for server_name, server_config in servers.items():
            if not isinstance(server_name, str) or not server_name.strip():
                raise ValidateErrorException("MCP服务器名称不能为空")
            if not isinstance(server_config, dict):
                raise ValidateErrorException(f"MCP服务器{server_name}配置必须是对象")
            if server_config.get("disabled") is True:
                continue

            cls._reject_unsupported_transport(server_name, server_config)
            transport = cls._normalize_transport(server_name, server_config.get("transport", "http"))
            url = cls._validate_url(server_name, server_config.get("url"))
            headers = cls._validate_headers(server_name, server_config.get("headers", {}) or {})
            description = server_config.get("description")
            if not isinstance(description, str) or not description.strip():
                description = f"MCP Streamable HTTP server: {url}"

            config = {
                "transport": transport,
                "url": url,
                "headers": headers,
            }
            normalized_servers.append({
                "name": server_name.strip(),
                "description": description,
                "config": config,
                "mcp_schema": json.dumps({
                    "mcpServers": {
                        server_name.strip(): {**server_config, **config}
                    }
                }, ensure_ascii=False, indent=2),
            })

        if len(normalized_servers) <= 0:
            raise ValidateErrorException("MCP配置中没有启用的服务器")

        return normalized_servers

    @classmethod
    def _reject_unsupported_transport(cls, server_name: str, server_config: dict[str, Any]) -> None:
        transport = server_config.get("transport")
        if transport in UNSUPPORTED_TRANSPORTS or any(key in server_config for key in ["command", "args", "env", "cwd"]):
            raise ValidateErrorException(
                f"当前仅支持Streamable HTTP MCP服务器，不支持本地stdio MCP：{server_name}"
            )

    @classmethod
    def _normalize_transport(cls, server_name: str, transport: Any) -> str:
        if not isinstance(transport, str):
            raise ValidateErrorException(f"MCP服务器{server_name}的transport必须是字符串")
        transport = transport.strip()
        if transport not in SUPPORTED_TRANSPORTS:
            raise ValidateErrorException(
                f"当前仅支持Streamable HTTP MCP服务器，不支持transport={transport}"
            )
        return "http"

    @classmethod
    def _validate_url(cls, server_name: str, url: Any) -> str:
        if not isinstance(url, str) or not url.strip():
            raise ValidateErrorException(f"MCP服务器{server_name}的url不能为空")
        url = McpProviderManager.normalize_url(url)
        parsed = urlparse(url)
        if parsed.scheme not in ["http", "https"] or not parsed.netloc:
            raise ValidateErrorException(f"MCP服务器{server_name}的url必须是HTTP/HTTPS地址")
        return url

    @classmethod
    def _validate_headers(cls, server_name: str, headers: Any) -> dict[str, str]:
        if not isinstance(headers, dict):
            raise ValidateErrorException(f"MCP服务器{server_name}的headers必须是对象")
        for key, value in headers.items():
            if not isinstance(key, str) or not isinstance(value, str):
                raise ValidateErrorException(f"MCP服务器{server_name}的headers键和值必须都是字符串")
        return headers

    def _load_remote_tools(self, server: dict[str, Any]) -> list[dict[str, Any]]:
        """连接远程MCP服务器并加载工具"""
        try:
            connection = self.mcp_provider_manager.build_connection(
                server["config"]["url"],
                server["config"]["headers"],
            )
            tools = self.mcp_provider_manager.load_tools(
                server["name"],
                connection,
                tool_name_prefix=False,
            )
            self._probe_known_credentials(server, tools)
        except Exception as e:
            raise ValidateErrorException(f"MCP服务器{server['name']}连接失败或工具列表读取失败: {str(e)}")

        if len(tools) <= 0:
            raise ValidateErrorException(f"MCP服务器{server['name']}没有返回可用工具")

        return [self._transform_langchain_tool(tool) for tool in tools]

    def _probe_known_credentials(self, server: dict[str, Any], tools: list[BaseTool]) -> None:
        """对部分会匿名返回工具列表的MCP服务做轻量凭证探测"""
        parsed = urlparse(server["config"]["url"])
        server_name = server["name"].lower()
        if parsed.netloc != "mcp.amap.com" and "amap" not in server_name:
            return

        probe_args_by_tool = {
            "maps_weather": {"city": "北京"},
            "maps_geo": {"address": "北京市"},
        }
        tool_map = {tool.name: tool for tool in tools}
        for tool_name, tool_args in probe_args_by_tool.items():
            tool = tool_map.get(tool_name)
            if tool is None:
                continue
            self.mcp_provider_manager.invoke_loaded_tool(tool, tool_args)
            return

    @classmethod
    def _transform_langchain_tool(cls, tool: BaseTool) -> dict[str, Any]:
        """将LangChain工具转换为可落库的MCP工具信息"""
        return {
            "name": tool.name,
            "description": tool.description or "",
            "input_schema": cls._dump_args_schema(tool.args_schema),
            "metadata": cls._jsonable(tool.metadata or {}),
        }

    @classmethod
    def _dump_args_schema(cls, args_schema: Any) -> dict[str, Any]:
        if isinstance(args_schema, dict):
            return cls._jsonable(args_schema)
        if isinstance(args_schema, type) and issubclass(args_schema, BaseModel):
            return args_schema.model_json_schema()
        if isinstance(args_schema, BaseModel):
            return args_schema.model_dump(mode="json")
        return {}

    @classmethod
    def _jsonable(cls, value: Any) -> Any:
        return json.loads(json.dumps(value, ensure_ascii=False, default=str))
