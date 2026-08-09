#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2026/6/22 
@Author : wzy
@File   : tool_entity
"""
from pydantic import BaseModel, Field


class McpToolEntity(BaseModel):
    """MCP工具实体信息，记录了创建LangChain工具所需的配置"""
    provider_id: str = Field(default="", description="MCP工具提供者id")
    name: str = Field(default="", description="MCP工具原始名称")
    description: str = Field(default="", description="MCP工具描述")
    url: str = Field(default="", description="MCP Streamable HTTP endpoint")
    headers: dict[str, str] = Field(default_factory=dict, description="MCP HTTP headers")
    input_schema: dict = Field(default_factory=dict, description="MCP工具输入JSON Schema")
    metadata: dict = Field(default_factory=dict, description="MCP工具元数据")
