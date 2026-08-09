#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2026/6/22 
@Author : wzy
@File   : mcp_tool_handler
"""
from dataclasses import dataclass
from uuid import UUID

from flask import request
from flask_login import login_required, current_user
from injector import inject

from internal.schema.mcp_tool_schema import (
    CreateMcpToolReq,
    GetMcpToolProviderResp,
    GetMcpToolProvidersWithPageReq,
    GetMcpToolProvidersWithPageResp,
    GetMcpToolResp,
    UpdateMcpToolProviderReq,
    ValidateMcpSchemaReq,
)
from internal.service import McpToolService
from pkg.paginator import PageModel
from pkg.response import validate_error_json, success_json, success_message


@inject
@dataclass
class McpToolHandler:
    """MCP插件处理器"""
    mcp_tool_service: McpToolService

    @login_required
    def get_mcp_tool_providers_with_page(self):
        req = GetMcpToolProvidersWithPageReq(request.args)
        if not req.validate():
            return validate_error_json(req.errors)

        providers, paginator = self.mcp_tool_service.get_mcp_tool_providers_with_page(req, current_user)
        resp = GetMcpToolProvidersWithPageResp(many=True)
        return success_json(PageModel(list=resp.dump(providers), paginator=paginator))

    @login_required
    def validate_mcp_schema(self):
        req = ValidateMcpSchemaReq()
        if not req.validate():
            return validate_error_json(req.errors)

        previews = self.mcp_tool_service.validate_mcp_schema(req.mcp_schema.data)
        return success_json(previews)

    @login_required
    def create_mcp_tool_provider(self):
        req = CreateMcpToolReq()
        if not req.validate():
            return validate_error_json(req.errors)

        self.mcp_tool_service.create_mcp_tools(req, current_user)
        return success_message("添加MCP服务器成功")

    @login_required
    def update_mcp_tool_provider(self, provider_id: UUID):
        req = UpdateMcpToolProviderReq()
        if not req.validate():
            return validate_error_json(req.errors)

        self.mcp_tool_service.update_mcp_tool_provider(provider_id, req, current_user)
        return success_message("更新MCP服务器成功")

    @login_required
    def get_mcp_tool_provider(self, provider_id: UUID):
        provider = self.mcp_tool_service.get_mcp_tool_provider(provider_id, current_user)
        resp = GetMcpToolProviderResp()
        return success_json(resp.dump(provider))

    @login_required
    def get_mcp_tool(self, provider_id: UUID, tool_name: str):
        tool = self.mcp_tool_service.get_mcp_tool(provider_id, tool_name, current_user)
        resp = GetMcpToolResp()
        return success_json(resp.dump(tool))

    @login_required
    def delete_mcp_tool_provider(self, provider_id: UUID):
        self.mcp_tool_service.delete_mcp_tool_provider(provider_id, current_user)
        return success_message("删除MCP服务器成功")
