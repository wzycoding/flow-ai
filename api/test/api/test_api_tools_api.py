#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
from uuid import uuid4

from pkg.response import HttpCode


OPENAPI_SCHEMA = {
    "server": "https://example.com",
    "description": "测试API工具",
    "paths": {
        "/location": {
            "get": {
                "description": "获取本地位置",
                "operationId": "GetLocationForIp",
                "parameters": [
                    {
                        "name": "ip",
                        "in": "query",
                        "description": "需要查询所在地的标准ip地址",
                        "required": False,
                        "type": "str",
                    }
                ],
            }
        }
    },
}


def test_validate_openapi_schema(client):
    invalid_resp = client.post("/api-tools/validate-openapi-schema", json={"openapi_schema": "123"})
    assert invalid_resp.status_code == 200
    assert invalid_resp.json["code"] == HttpCode.VALIDATE_ERROR

    valid_resp = client.post("/api-tools/validate-openapi-schema", json={"openapi_schema": json.dumps(OPENAPI_SCHEMA)})
    assert valid_resp.status_code == 200
    assert valid_resp.json["code"] == HttpCode.SUCCESS


def test_api_tool_provider_crud(client):
    provider_name = f"pytest_api_tool_{uuid4().hex[:8]}"
    payload = {
        "name": provider_name,
        "icon": "https://img.aiflowline.cn/blog/20260806162348866.png?imageSlim",
        "openapi_schema": json.dumps(OPENAPI_SCHEMA),
        "headers": [{"key": "Authorization", "value": "Bearer test-token"}],
    }

    create_resp = client.post("/api-tools", json=payload)
    assert create_resp.status_code == 200
    assert create_resp.json["code"] == HttpCode.SUCCESS

    list_resp = client.get("/api-tools", query_string={"search_word": provider_name})
    assert list_resp.status_code == 200
    assert list_resp.json["code"] == HttpCode.SUCCESS
    provider = list_resp.json["data"]["list"][0]
    provider_id = provider["id"]
    assert provider["name"] == provider_name

    get_provider_resp = client.get(f"/api-tools/{provider_id}")
    assert get_provider_resp.status_code == 200
    assert get_provider_resp.json["code"] == HttpCode.SUCCESS

    get_tool_resp = client.get(f"/api-tools/{provider_id}/tools/GetLocationForIp")
    assert get_tool_resp.status_code == 200
    assert get_tool_resp.json["code"] == HttpCode.SUCCESS
    assert get_tool_resp.json["data"]["inputs"][0]["name"] == "ip"

    delete_resp = client.post(f"/api-tools/{provider_id}/delete")
    assert delete_resp.status_code == 200
    assert delete_resp.json["code"] == HttpCode.SUCCESS
