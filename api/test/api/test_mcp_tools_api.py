#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
from uuid import uuid4

import pytest
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from internal.core.tools.mcp_tools.providers import McpProviderManager
from pkg.response import HttpCode


class SearchArgs(BaseModel):
    query: str = Field(..., description="搜索关键词")


class EchoArgs(BaseModel):
    text: str = Field(..., description="回显文本")


def _fake_mcp_tools(server_name: str, connection: dict, tool_name_prefix: bool = False):
    prefix = f"{server_name}_" if tool_name_prefix else ""

    def search(query: str) -> str:
        return f"search:{query}"

    def echo(text: str) -> str:
        return text

    return [
        StructuredTool.from_function(
            func=search,
            name=f"{prefix}search",
            description=f"Search from {connection['url']}",
            args_schema=SearchArgs,
        ),
        StructuredTool.from_function(
            func=echo,
            name=f"{prefix}echo",
            description="Echo text",
            args_schema=EchoArgs,
        ),
    ]


@pytest.fixture(autouse=True)
def mock_mcp_manager(monkeypatch):
    monkeypatch.setattr(McpProviderManager, "load_tools", staticmethod(_fake_mcp_tools))


def _schema(server_name: str, url: str = "https://example.com/mcp", **kwargs) -> str:
    return json.dumps({
        "mcpServers": {
            server_name: {
                "transport": kwargs.pop("transport", "streamable-http"),
                "url": url,
                "headers": kwargs.pop("headers", {"Authorization": "Bearer test"}),
                "description": kwargs.pop("description", "pytest MCP server"),
                **kwargs,
            }
        }
    })


def _create_provider(client, server_name: str | None = None) -> dict:
    server_name = server_name or f"pytest_mcp_{uuid4().hex[:8]}"
    create_resp = client.post("/mcp-tools", json={"mcp_schema": _schema(server_name)})
    assert create_resp.status_code == 200
    assert create_resp.json["code"] == HttpCode.SUCCESS

    list_resp = client.get("/mcp-tools", query_string={"search_word": server_name})
    assert list_resp.status_code == 200
    assert list_resp.json["code"] == HttpCode.SUCCESS
    assert len(list_resp.json["data"]["list"]) == 1
    return list_resp.json["data"]["list"][0]


def test_validate_mcp_schema_supports_http_headers_and_multi_server(client):
    mcp_schema = json.dumps({
        "mcpServers": {
            f"pytest_mcp_a_{uuid4().hex[:6]}": {
                "transport": "http",
                "url": "https://example.com/a/mcp",
                "headers": {"X-Test": "one"},
            },
            f"pytest_mcp_b_{uuid4().hex[:6]}": {
                "transport": "streamhttp",
                "url": "https://example.com/b/mcp",
            },
        }
    })

    resp = client.post("/mcp-tools/validate-mcp-schema", json={"mcp_schema": mcp_schema})

    assert resp.status_code == 200
    assert resp.json["code"] == HttpCode.SUCCESS
    assert len(resp.json["data"]) == 2
    assert resp.json["data"][0]["config"]["transport"] == "http"
    assert resp.json["data"][0]["tools"][0]["name"] == "search"


def test_mcp_schema_normalizes_query_value_spaces():
    servers = McpProviderManager.normalize_url(
        "https://mcp.amap.com/mcp?key= test-key"
    )
    assert servers == "https://mcp.amap.com/mcp?key=test-key"


def test_validate_mcp_schema_rejects_amap_invalid_key_probe(client, monkeypatch):
    def amap_tools(server_name: str, connection: dict, tool_name_prefix: bool = False):
        prefix = f"{server_name}_" if tool_name_prefix else ""

        def maps_weather(city: str) -> str:
            return city

        return [StructuredTool.from_function(
            func=maps_weather,
            name=f"{prefix}maps_weather",
            description="根据城市名称或者标准adcode查询指定城市的天气",
            args_schema=SearchArgs,
        )]

    def fail_probe(tool, kwargs):
        raise Exception("API 调用失败：INVALID_USER_KEY")

    monkeypatch.setattr(McpProviderManager, "load_tools", staticmethod(amap_tools))
    monkeypatch.setattr(McpProviderManager, "invoke_loaded_tool", staticmethod(fail_probe))
    mcp_schema = _schema(
        f"amap_mcp_{uuid4().hex[:8]}",
        url="https://mcp.amap.com/mcp?key=fake-key",
    )

    resp = client.post("/mcp-tools/validate-mcp-schema", json={"mcp_schema": mcp_schema})

    assert resp.status_code == 200
    assert resp.json["code"] == HttpCode.VALIDATE_ERROR
    assert "INVALID_USER_KEY" in resp.json["message"]


@pytest.mark.parametrize("server_config", [
    {"transport": "stdio", "command": "uvx", "args": ["demo"]},
    {"transport": "sse", "url": "https://example.com/sse"},
    {"transport": "websocket", "url": "wss://example.com/mcp"},
    {"transport": "http", "url": "ftp://example.com/mcp"},
    {"transport": "http", "url": "https://example.com/mcp", "headers": {"X-Test": 1}},
])
def test_validate_mcp_schema_rejects_unsupported_configs(client, server_config):
    mcp_schema = json.dumps({"mcpServers": {f"pytest_mcp_{uuid4().hex[:8]}": server_config}})

    resp = client.post("/mcp-tools/validate-mcp-schema", json={"mcp_schema": mcp_schema})

    assert resp.status_code == 200
    assert resp.json["code"] == HttpCode.VALIDATE_ERROR


def test_mcp_tool_provider_crud(client):
    provider = _create_provider(client)
    provider_id = provider["id"]
    assert provider["transport"] == "http"
    search_tool = next(tool for tool in provider["tools"] if tool["name"] == "search")
    assert search_tool["inputs"][0]["name"] == "query"

    get_provider_resp = client.get(f"/mcp-tools/{provider_id}")
    assert get_provider_resp.status_code == 200
    assert get_provider_resp.json["code"] == HttpCode.SUCCESS
    assert get_provider_resp.json["data"]["headers"]["Authorization"] == "Bearer test"

    get_tool_resp = client.get(f"/mcp-tools/{provider_id}/tools/search")
    assert get_tool_resp.status_code == 200
    assert get_tool_resp.json["code"] == HttpCode.SUCCESS
    assert get_tool_resp.json["data"]["provider"]["id"] == provider_id
    assert get_tool_resp.json["data"]["inputs"][0]["name"] == "query"

    updated_name = f"pytest_mcp_updated_{uuid4().hex[:8]}"
    update_resp = client.post(f"/mcp-tools/{provider_id}", json={
        "mcp_schema": _schema(updated_name, url="https://example.com/updated/mcp")
    })
    assert update_resp.status_code == 200
    assert update_resp.json["code"] == HttpCode.SUCCESS

    get_updated_resp = client.get(f"/mcp-tools/{provider_id}")
    assert get_updated_resp.json["data"]["name"] == updated_name
    assert len(get_updated_resp.json["data"]["tools"]) == 2

    delete_resp = client.post(f"/mcp-tools/{provider_id}/delete")
    assert delete_resp.status_code == 200
    assert delete_resp.json["code"] == HttpCode.SUCCESS


def test_app_draft_config_accepts_mcp_tool_and_keeps_limits(client):
    provider = _create_provider(client)

    create_app_resp = client.post("/apps", json={
        "name": f"pytest_app_mcp_{uuid4().hex[:8]}",
        "icon": "https://img.aiflowline.cn/blog/20260806162348866.png?imageSlim",
        "description": "pytest MCP app",
    })
    assert create_app_resp.status_code == 200
    app_id = create_app_resp.json["data"]["id"]

    update_resp = client.post(f"/apps/{app_id}/draft-app-config", json={
        "tools": [{
            "type": "mcp_tool",
            "provider_id": provider["id"],
            "tool_id": "search",
            "params": {},
        }]
    })
    assert update_resp.status_code == 200
    assert update_resp.json["code"] == HttpCode.SUCCESS

    get_resp = client.get(f"/apps/{app_id}/draft-app-config")
    assert get_resp.status_code == 200
    assert get_resp.json["data"]["tools"][0]["type"] == "mcp_tool"
    assert get_resp.json["data"]["tools"][0]["provider"]["id"] == provider["id"]

    repeated = [{
        "type": "mcp_tool",
        "provider_id": provider["id"],
        "tool_id": "search",
        "params": {},
    } for _ in range(6)]
    limit_resp = client.post(f"/apps/{app_id}/draft-app-config", json={"tools": repeated})
    assert limit_resp.status_code == 200
    assert limit_resp.json["code"] == HttpCode.VALIDATE_ERROR


def test_workflow_draft_graph_populates_mcp_tool_meta(client):
    provider = _create_provider(client)

    create_resp = client.post("/workflows", json={
        "name": f"pytest_workflow_mcp_{uuid4().hex[:8]}",
        "tool_call_name": f"pytest_workflow_mcp_{uuid4().hex[:8]}",
        "icon": "https://img.aiflowline.cn/blog/20260806162348866.png?imageSlim",
        "description": "pytest MCP workflow",
    })
    assert create_resp.status_code == 200
    workflow_id = create_resp.json["data"]["id"]

    start_id = str(uuid4())
    tool_id = str(uuid4())
    end_id = str(uuid4())
    graph = {
        "nodes": [
            {
                "id": start_id,
                "node_type": "start",
                "title": "开始节点",
                "description": "开始节点",
                "position": {"x": 0, "y": 0},
                "inputs": [{
                    "name": "query",
                    "description": "测试输入",
                    "required": True,
                    "type": "string",
                    "value": {"type": "generated", "content": ""},
                }],
            },
            {
                "id": tool_id,
                "node_type": "tool",
                "title": "MCP工具节点",
                "description": "MCP工具节点",
                "position": {"x": 320, "y": 0},
                "tool_type": "mcp_tool",
                "provider_id": provider["id"],
                "tool_id": "search",
                "params": {},
                "inputs": [{
                    "name": "query",
                    "description": "测试输入",
                    "required": True,
                    "type": "string",
                    "value": {
                        "type": "ref",
                        "content": {
                            "ref_node_id": start_id,
                            "ref_var_name": "query",
                        },
                    },
                    "meta": {},
                }],
            },
            {
                "id": end_id,
                "node_type": "end",
                "title": "结束节点",
                "description": "结束节点",
                "position": {"x": 640, "y": 0},
                "outputs": [{
                    "name": "output",
                    "description": "测试输出",
                    "required": True,
                    "type": "string",
                    "value": {
                        "type": "ref",
                        "content": {
                            "ref_node_id": tool_id,
                            "ref_var_name": "text",
                        },
                    },
                }],
            },
        ],
        "edges": [
            {
                "id": str(uuid4()),
                "source": start_id,
                "source_type": "start",
                "source_handle_id": None,
                "target": tool_id,
                "target_type": "tool",
            },
            {
                "id": str(uuid4()),
                "source": tool_id,
                "source_type": "tool",
                "source_handle_id": None,
                "target": end_id,
                "target_type": "end",
            },
        ],
    }

    update_graph_resp = client.post(f"/workflows/{workflow_id}/draft-graph", json=graph)
    assert update_graph_resp.status_code == 200
    assert update_graph_resp.json["code"] == HttpCode.SUCCESS

    get_graph_resp = client.get(f"/workflows/{workflow_id}/draft-graph")
    assert get_graph_resp.status_code == 200
    tool_nodes = [
        node for node in get_graph_resp.json["data"]["nodes"]
        if node["node_type"] == "tool"
    ]
    assert tool_nodes[0]["meta"]["type"] == "mcp_tool"
    assert tool_nodes[0]["meta"]["provider"]["id"] == provider["id"]
