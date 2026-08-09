#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2026/6/22 
@Author : wzy
@File   : mcp_tool_schema
"""
from typing import Any

from flask_wtf import FlaskForm
from marshmallow import Schema, fields, pre_dump
from wtforms import StringField
from wtforms.validators import DataRequired, Optional

from internal.model import McpToolProvider, McpTool
from internal.lib.helper import datetime_to_timestamp
from pkg.paginator import PaginatorReq


JSON_SCHEMA_TYPE_MAP = {
    "string": "str",
    "integer": "int",
    "number": "float",
    "boolean": "bool",
}


def transform_mcp_input_schema(input_schema: dict[str, Any]) -> list[dict[str, Any]]:
    """将MCP JSON Schema转换为前端已有工具参数展示结构"""
    properties = input_schema.get("properties", {})
    required = set(input_schema.get("required", []))
    if not isinstance(properties, dict):
        return []

    inputs = []
    for name, property_schema in properties.items():
        if not isinstance(property_schema, dict):
            property_schema = {}
        json_type = property_schema.get("type", "string")
        if isinstance(json_type, list):
            json_type = next((item for item in json_type if item != "null"), "string")
        inputs.append({
            "name": name,
            "type": JSON_SCHEMA_TYPE_MAP.get(json_type, "str"),
            "required": name in required,
            "description": property_schema.get("description", ""),
            "schema": property_schema,
        })

    return inputs


class ValidateMcpSchemaReq(FlaskForm):
    """校验MCP配置字符串请求"""
    mcp_schema = StringField("mcp_schema", validators=[
        DataRequired(message="mcp_schema字符串不能为空")
    ])


class GetMcpToolProvidersWithPageReq(PaginatorReq):
    """获取MCP工具提供者分页列表请求"""
    search_word = StringField("search_word", validators=[Optional()])


class CreateMcpToolReq(FlaskForm):
    """创建MCP工具请求"""
    mcp_schema = StringField("mcp_schema", validators=[
        DataRequired(message="mcp_schema字符串不能为空")
    ])


class UpdateMcpToolProviderReq(FlaskForm):
    """更新MCP工具提供者请求"""
    mcp_schema = StringField("mcp_schema", validators=[
        DataRequired(message="mcp_schema字符串不能为空")
    ])


class GetMcpToolProviderResp(Schema):
    """获取MCP工具提供者响应信息"""
    id = fields.UUID()
    name = fields.String()
    description = fields.String()
    transport = fields.String()
    url = fields.String()
    headers = fields.Dict()
    config = fields.Dict()
    mcp_schema = fields.String()
    tools = fields.List(fields.Dict, dump_default=[])
    updated_at = fields.Integer(dump_default=0)
    created_at = fields.Integer(dump_default=0)

    @pre_dump
    def process_data(self, data: McpToolProvider, **kwargs):
        return {
            "id": data.id,
            "name": data.name,
            "description": data.description,
            "transport": data.transport,
            "url": data.url,
            "headers": data.headers,
            "config": data.config,
            "mcp_schema": data.mcp_schema,
            "tools": [{
                "id": tool.id,
                "name": tool.name,
                "description": tool.description,
                "inputs": transform_mcp_input_schema(tool.input_schema),
                "input_schema": tool.input_schema,
            } for tool in data.tools],
            "updated_at": datetime_to_timestamp(data.updated_at),
            "created_at": datetime_to_timestamp(data.created_at),
        }


class GetMcpToolResp(Schema):
    """获取MCP工具参数详情响应"""
    id = fields.UUID()
    name = fields.String()
    description = fields.String()
    inputs = fields.List(fields.Dict, dump_default=[])
    input_schema = fields.Dict()
    metadata = fields.Dict()
    provider = fields.Dict()

    @pre_dump
    def process_data(self, data: McpTool, **kwargs):
        provider = data.provider
        return {
            "id": data.id,
            "name": data.name,
            "description": data.description,
            "inputs": transform_mcp_input_schema(data.input_schema),
            "input_schema": data.input_schema,
            "metadata": data.tool_metadata,
            "provider": {
                "id": provider.id,
                "name": provider.name,
                "label": provider.name,
                "icon": "",
                "description": provider.description,
                "transport": provider.transport,
                "url": provider.url,
                "headers": provider.headers,
            },
        }


class GetMcpToolProvidersWithPageResp(Schema):
    """获取MCP工具提供者分页列表数据响应"""
    id = fields.UUID()
    name = fields.String()
    description = fields.String()
    transport = fields.String()
    url = fields.String()
    headers = fields.Dict()
    tools = fields.List(fields.Dict, dump_default=[])
    updated_at = fields.Integer(dump_default=0)
    created_at = fields.Integer(dump_default=0)

    @pre_dump
    def process_data(self, data: McpToolProvider, **kwargs):
        return {
            "id": data.id,
            "name": data.name,
            "description": data.description,
            "transport": data.transport,
            "url": data.url,
            "headers": data.headers,
            "tools": [{
                "id": tool.id,
                "name": tool.name,
                "description": tool.description,
                "inputs": transform_mcp_input_schema(tool.input_schema),
                "input_schema": tool.input_schema,
            } for tool in data.tools],
            "updated_at": datetime_to_timestamp(data.updated_at),
            "created_at": datetime_to_timestamp(data.created_at),
        }
