#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import os
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

import pytest

from pkg.response import HttpCode


OPENAPI_SCHEMA = {
    "server": "https://example.com",
    "description": "router contract provider",
    "paths": {
        "/location": {
            "get": {
                "description": "Get location",
                "operationId": "GetLocationForIp",
                "parameters": [
                    {
                        "name": "ip",
                        "in": "query",
                        "description": "IP address",
                        "required": False,
                        "type": "str",
                    }
                ],
            }
        }
    },
}


@dataclass(frozen=True)
class RouteCase:
    method: str
    rule: str
    path: str
    json: dict[str, Any] | None = None
    query: dict[str, Any] | None = None
    auth: str = "jwt"
    content: str = "json"
    expected_codes: tuple[HttpCode, ...] | None = (HttpCode.SUCCESS,)


BUSINESS_FAILURE_CODES = (
    HttpCode.FAIL,
    HttpCode.NOT_FOUND,
    HttpCode.FORBIDDEN,
    HttpCode.UNAUTHORIZED,
)
VALIDATION_CODES = (HttpCode.VALIDATE_ERROR,)
RESOURCE_FAILURE_CODES = BUSINESS_FAILURE_CODES + VALIDATION_CODES


ROUTE_CASES = [
    RouteCase("GET", "/ping", "/ping"),
    RouteCase("GET", "/apps", "/apps", query={"current_page": 1, "page_size": 20}),
    RouteCase("POST", "/apps", "/apps", json={
        "name": "router_app_{suffix}",
        "icon": "https://img.aiflowline.cn/blog/20260806162348866.png?imageSlim",
        "description": "router contract app",
    }),
    RouteCase("GET", "/apps/<uuid:app_id>", "/apps/{app_id}"),
    RouteCase("POST", "/apps/<uuid:app_id>", "/apps/{app_id}", json={
        "name": "router_app_update_{suffix}",
        "icon": "https://img.aiflowline.cn/blog/20260806162348866.png?imageSlim",
        "description": "router contract app updated",
    }),
    RouteCase("POST", "/apps/<uuid:app_id>/delete", "/apps/{missing_id}/delete", expected_codes=RESOURCE_FAILURE_CODES),
    RouteCase("POST", "/apps/<uuid:app_id>/copy", "/apps/{app_id}/copy"),
    RouteCase("GET", "/apps/<uuid:app_id>/draft-app-config", "/apps/{app_id}/draft-app-config"),
    RouteCase("POST", "/apps/<uuid:app_id>/draft-app-config", "/apps/{app_id}/draft-app-config", json={}, expected_codes=VALIDATION_CODES),
    RouteCase("POST", "/apps/<uuid:app_id>/publish", "/apps/{app_id}/publish", expected_codes=(HttpCode.SUCCESS, HttpCode.FAIL)),
    RouteCase("POST", "/apps/<uuid:app_id>/cancel-publish", "/apps/{app_id}/cancel-publish", expected_codes=(HttpCode.SUCCESS, HttpCode.FAIL)),
    RouteCase("GET", "/apps/<uuid:app_id>/publish-histories", "/apps/{app_id}/publish-histories"),
    RouteCase("POST", "/apps/<uuid:app_id>/fallback-history", "/apps/{app_id}/fallback-history", json={}, expected_codes=VALIDATION_CODES),
    RouteCase("GET", "/apps/<uuid:app_id>/summary", "/apps/{app_id}/summary", expected_codes=(HttpCode.FAIL,)),
    RouteCase("POST", "/apps/<uuid:app_id>/summary", "/apps/{app_id}/summary", json={"summary": "router contract summary"}, expected_codes=(HttpCode.FAIL,)),
    RouteCase("POST", "/apps/<uuid:app_id>/conversations/delete-debug-conversation", "/apps/{app_id}/conversations/delete-debug-conversation"),
    RouteCase("POST", "/apps/<uuid:app_id>/conversations", "/apps/{app_id}/conversations", json={}, expected_codes=VALIDATION_CODES),
    RouteCase("POST", "/apps/<uuid:app_id>/conversations/tasks/<uuid:task_id>/stop", "/apps/{app_id}/conversations/tasks/{task_id}/stop"),
    RouteCase("GET", "/apps/<uuid:app_id>/conversations/messages", "/apps/{app_id}/conversations/messages", query={"current_page": 1, "page_size": 20}),
    RouteCase("GET", "/apps/<uuid:app_id>/published-config", "/apps/{app_id}/published-config", expected_codes=(HttpCode.SUCCESS, HttpCode.FAIL)),
    RouteCase("POST", "/apps/<uuid:app_id>/published-config/regenerate-web-app-token", "/apps/{app_id}/published-config/regenerate-web-app-token", expected_codes=(HttpCode.FAIL,)),
    RouteCase("GET", "/builtin-tools", "/builtin-tools"),
    RouteCase("GET", "/builtin-tools/<string:provider_name>/tools/<string:tool_name>", "/builtin-tools/google/tools/google_serper"),
    RouteCase("GET", "/builtin-tools/<string:provider_name>/icon", "/builtin-tools/google/icon", content="binary", expected_codes=None),
    RouteCase("GET", "/builtin-tools/categories", "/builtin-tools/categories"),
    RouteCase("GET", "/api-tools", "/api-tools", query={"current_page": 1, "page_size": 20}),
    RouteCase("POST", "/api-tools/validate-openapi-schema", "/api-tools/validate-openapi-schema", json={"openapi_schema": "{openapi_schema_json}"}),
    RouteCase("POST", "/api-tools", "/api-tools", json={
        "name": "rt_provider_{suffix}",
        "icon": "https://img.aiflowline.cn/blog/20260806162348866.png?imageSlim",
        "openapi_schema": "{openapi_schema_json}",
        "headers": [],
    }),
    RouteCase("GET", "/api-tools/<uuid:provider_id>", "/api-tools/{provider_id}"),
    RouteCase("POST", "/api-tools/<uuid:provider_id>", "/api-tools/{provider_id}", json={
        "name": "rt_provider_u_{suffix}",
        "icon": "https://img.aiflowline.cn/blog/20260806162348866.png?imageSlim",
        "openapi_schema": "{openapi_schema_json}",
        "headers": [],
    }),
    RouteCase("GET", "/api-tools/<uuid:provider_id>/tools/<string:tool_name>", "/api-tools/{provider_id}/tools/GetLocationForIp"),
    RouteCase("POST", "/api-tools/<uuid:provider_id>/delete", "/api-tools/{missing_id}/delete", expected_codes=RESOURCE_FAILURE_CODES),
    RouteCase("POST", "/upload-files/file", "/upload-files/file", expected_codes=VALIDATION_CODES),
    RouteCase("POST", "/upload-files/image", "/upload-files/image", expected_codes=VALIDATION_CODES),
    RouteCase("GET", "/datasets", "/datasets", query={"current_page": 1, "page_size": 20}),
    RouteCase("POST", "/datasets", "/datasets", json={
        "name": "router_dataset_{suffix}",
        "icon": "https://img.aiflowline.cn/blog/20260806162348866.png?imageSlim",
        "description": "router contract dataset",
    }),
    RouteCase("GET", "/datasets/<uuid:dataset_id>", "/datasets/{dataset_id}"),
    RouteCase("POST", "/datasets/<uuid:dataset_id>", "/datasets/{dataset_id}", json={
        "name": "router_dataset_update_{suffix}",
        "icon": "https://img.aiflowline.cn/blog/20260806162348866.png?imageSlim",
        "description": "router contract dataset updated",
    }),
    RouteCase("GET", "/datasets/<uuid:dataset_id>/queries", "/datasets/{dataset_id}/queries", query={"current_page": 1, "page_size": 20}),
    RouteCase("POST", "/datasets/<uuid:dataset_id>/delete", "/datasets/{missing_id}/delete", expected_codes=RESOURCE_FAILURE_CODES),
    RouteCase("GET", "/datasets/<uuid:dataset_id>/documents", "/datasets/{dataset_id}/documents", query={"current_page": 1, "page_size": 20}),
    RouteCase("POST", "/datasets/<uuid:dataset_id>/documents", "/datasets/{dataset_id}/documents", json={}, expected_codes=VALIDATION_CODES),
    RouteCase("GET", "/datasets/<uuid:dataset_id>/documents/<uuid:document_id>", "/datasets/{dataset_id}/documents/{missing_id}", expected_codes=RESOURCE_FAILURE_CODES),
    RouteCase("POST", "/datasets/<uuid:dataset_id>/documents/<uuid:document_id>/name", "/datasets/{dataset_id}/documents/{missing_id}/name", json={"name": "router document"}, expected_codes=RESOURCE_FAILURE_CODES),
    RouteCase("POST", "/datasets/<uuid:dataset_id>/documents/<uuid:document_id>/enabled", "/datasets/{dataset_id}/documents/{missing_id}/enabled", json={"enabled": True}, expected_codes=RESOURCE_FAILURE_CODES),
    RouteCase("POST", "/datasets/<uuid:dataset_id>/documents/<uuid:document_id>/delete", "/datasets/{dataset_id}/documents/{missing_id}/delete", expected_codes=RESOURCE_FAILURE_CODES),
    RouteCase("GET", "/datasets/<uuid:dataset_id>/documents/batch/<string:batch>", "/datasets/{dataset_id}/documents/batch/router-batch", expected_codes=RESOURCE_FAILURE_CODES),
    RouteCase("GET", "/datasets/<uuid:dataset_id>/documents/<uuid:document_id>/segments", "/datasets/{dataset_id}/documents/{missing_id}/segments", query={"current_page": 1, "page_size": 20}, expected_codes=RESOURCE_FAILURE_CODES),
    RouteCase("POST", "/datasets/<uuid:dataset_id>/documents/<uuid:document_id>/segments", "/datasets/{dataset_id}/documents/{missing_id}/segments", json={"content": "router segment", "keywords": []}, expected_codes=RESOURCE_FAILURE_CODES),
    RouteCase("GET", "/datasets/<uuid:dataset_id>/documents/<uuid:document_id>/segments/<uuid:segment_id>", "/datasets/{dataset_id}/documents/{missing_id}/segments/{missing_segment_id}", expected_codes=RESOURCE_FAILURE_CODES),
    RouteCase("POST", "/datasets/<uuid:dataset_id>/documents/<uuid:document_id>/segments/<uuid:segment_id>", "/datasets/{dataset_id}/documents/{missing_id}/segments/{missing_segment_id}", json={"content": "router segment update", "keywords": []}, expected_codes=RESOURCE_FAILURE_CODES),
    RouteCase("POST", "/datasets/<uuid:dataset_id>/documents/<uuid:document_id>/segments/<uuid:segment_id>/enabled", "/datasets/{dataset_id}/documents/{missing_id}/segments/{missing_segment_id}/enabled", json={"enabled": True}, expected_codes=RESOURCE_FAILURE_CODES),
    RouteCase("POST", "/datasets/<uuid:dataset_id>/documents/<uuid:document_id>/segments/<uuid:segment_id>/delete", "/datasets/{dataset_id}/documents/{missing_id}/segments/{missing_segment_id}/delete", expected_codes=RESOURCE_FAILURE_CODES),
    RouteCase("POST", "/datasets/<uuid:dataset_id>/hit", "/datasets/{dataset_id}/hit", json={}, expected_codes=VALIDATION_CODES),
    RouteCase("GET", "/oauth/<string:provider_name>", "/oauth/github"),
    RouteCase("POST", "/oauth/authorize/<string:provider_name>", "/oauth/authorize/github", json={}, expected_codes=VALIDATION_CODES),
    RouteCase("POST", "/auth/password-login", "/auth/password-login", json={"email": "{account_email}", "password": "{account_password}"}),
    RouteCase("POST", "/auth/logout", "/auth/logout"),
    RouteCase("GET", "/account", "/account"),
    RouteCase("POST", "/account/password", "/account/password", json={"password": "xxx123"}),
    RouteCase("POST", "/account/name", "/account/name", json={"name": "router_{suffix}"}),
    RouteCase("POST", "/account/avatar", "/account/avatar", json={"avatar": "https://img.aiflowline.cn/blog/20260806162348866.png?imageSlim"}),
    RouteCase("POST", "/ai/optimize-prompt", "/ai/optimize-prompt", json={}, expected_codes=VALIDATION_CODES),
    RouteCase("POST", "/ai/suggested-questions", "/ai/suggested-questions", json={}, expected_codes=VALIDATION_CODES),
    RouteCase("GET", "/openapi/api-keys", "/openapi/api-keys", query={"current_page": 1, "page_size": 20}),
    RouteCase("POST", "/openapi/api-keys", "/openapi/api-keys", json={"is_active": True, "remark": "router contract key"}),
    RouteCase("POST", "/openapi/api-keys/<uuid:api_key_id>", "/openapi/api-keys/{api_key_id}", json={"is_active": True, "remark": "router contract key updated"}),
    RouteCase("POST", "/openapi/api-keys/<uuid:api_key_id>/is-active", "/openapi/api-keys/{api_key_id}/is-active", json={"is_active": True}),
    RouteCase("POST", "/openapi/api-keys/<uuid:api_key_id>/delete", "/openapi/api-keys/{missing_id}/delete", expected_codes=RESOURCE_FAILURE_CODES),
    RouteCase("POST", "/openapi/chat", "/openapi/chat", json={}, auth="api_key", expected_codes=VALIDATION_CODES),
    RouteCase("GET", "/builtin-apps/categories", "/builtin-apps/categories"),
    RouteCase("GET", "/builtin-apps", "/builtin-apps"),
    RouteCase("POST", "/builtin-apps/add-builtin-app-to-space", "/builtin-apps/add-builtin-app-to-space", json={}, expected_codes=VALIDATION_CODES),
    RouteCase("GET", "/workflows", "/workflows", query={"current_page": 1, "page_size": 20}),
    RouteCase("POST", "/workflows", "/workflows", json={
        "name": "router_workflow_{suffix}",
        "tool_call_name": "router_workflow_{suffix}",
        "icon": "https://img.aiflowline.cn/blog/20260806162348866.png?imageSlim",
        "description": "router contract workflow",
    }),
    RouteCase("GET", "/workflows/<uuid:workflow_id>", "/workflows/{workflow_id}"),
    RouteCase("POST", "/workflows/<uuid:workflow_id>", "/workflows/{workflow_id}", json={
        "name": "router_workflow_update_{suffix}",
        "tool_call_name": "router_workflow_update_{suffix}",
        "icon": "https://img.aiflowline.cn/blog/20260806162348866.png?imageSlim",
        "description": "router contract workflow updated",
    }),
    RouteCase("POST", "/workflows/<uuid:workflow_id>/delete", "/workflows/{missing_id}/delete", expected_codes=RESOURCE_FAILURE_CODES),
    RouteCase("GET", "/workflows/<uuid:workflow_id>/draft-graph", "/workflows/{workflow_id}/draft-graph"),
    RouteCase("POST", "/workflows/<uuid:workflow_id>/draft-graph", "/workflows/{workflow_id}/draft-graph", json={"nodes": [], "edges": []}, expected_codes=(HttpCode.SUCCESS, HttpCode.FAIL)),
    RouteCase("POST", "/workflows/<uuid:workflow_id>/debug", "/workflows/{missing_id}/debug", json={}, expected_codes=RESOURCE_FAILURE_CODES),
    RouteCase("POST", "/workflows/<uuid:workflow_id>/publish", "/workflows/{missing_id}/publish", expected_codes=RESOURCE_FAILURE_CODES),
    RouteCase("POST", "/workflows/<uuid:workflow_id>/cancel-publish", "/workflows/{missing_id}/cancel-publish", expected_codes=RESOURCE_FAILURE_CODES),
    RouteCase("GET", "/language-models", "/language-models"),
    RouteCase("GET", "/language-models/<string:provider_name>/icon", "/language-models/openai/icon", content="binary", expected_codes=None),
    RouteCase("GET", "/language-models/<string:provider_name>/<string:model_name>", "/language-models/openai/gpt-4o-mini"),
    RouteCase("POST", "/assistant-agent/chat", "/assistant-agent/chat", json={}, expected_codes=VALIDATION_CODES),
    RouteCase("POST", "/assistant-agent/chat/<uuid:task_id>/stop", "/assistant-agent/chat/{task_id}/stop"),
    RouteCase("GET", "/assistant-agent/messages", "/assistant-agent/messages", query={"current_page": 1, "page_size": 20}),
    RouteCase("POST", "/assistant-agent/delete-conversation", "/assistant-agent/delete-conversation"),
    RouteCase("GET", "/analysis/<uuid:app_id>", "/analysis/{app_id}"),
    RouteCase("GET", "/web-apps/<string:token>", "/web-apps/missing-token", expected_codes=RESOURCE_FAILURE_CODES),
    RouteCase("POST", "/web-apps/<string:token>/chat", "/web-apps/missing-token/chat", json={"query": "hello"}, content="stream", expected_codes=None),
    RouteCase("POST", "/web-apps/<string:token>/chat/<uuid:task_id>/stop", "/web-apps/missing-token/chat/{task_id}/stop", expected_codes=RESOURCE_FAILURE_CODES),
    RouteCase("GET", "/web-apps/<string:token>/conversations", "/web-apps/missing-token/conversations", expected_codes=RESOURCE_FAILURE_CODES),
    RouteCase("GET", "/conversations/<uuid:conversation_id>/messages", "/conversations/{missing_id}/messages", query={"current_page": 1, "page_size": 20}, expected_codes=RESOURCE_FAILURE_CODES),
    RouteCase("POST", "/conversations/<uuid:conversation_id>/delete", "/conversations/{missing_id}/delete", expected_codes=RESOURCE_FAILURE_CODES),
    RouteCase("POST", "/conversations/<uuid:conversation_id>/messages/<uuid:message_id>/delete", "/conversations/{missing_id}/messages/{missing_message_id}/delete", expected_codes=RESOURCE_FAILURE_CODES),
    RouteCase("GET", "/conversations/<uuid:conversation_id>/name", "/conversations/{missing_id}/name", expected_codes=RESOURCE_FAILURE_CODES),
    RouteCase("POST", "/conversations/<uuid:conversation_id>/name", "/conversations/{missing_id}/name", json={"name": "router conversation"}, expected_codes=RESOURCE_FAILURE_CODES),
    RouteCase("POST", "/conversations/<uuid:conversation_id>/is-pinned", "/conversations/{missing_id}/is-pinned", json={"is_pinned": True}, expected_codes=RESOURCE_FAILURE_CODES),
    RouteCase("POST", "/audio/audio-to-text", "/audio/audio-to-text", expected_codes=VALIDATION_CODES),
    RouteCase("POST", "/audio/message-to-audio", "/audio/message-to-audio", json={}, expected_codes=VALIDATION_CODES),
    RouteCase("GET", "/platform/<uuid:app_id>/wechat-config", "/platform/{app_id}/wechat-config"),
    RouteCase("POST", "/platform/<uuid:app_id>/wechat-config", "/platform/{app_id}/wechat-config", json={
        "wechat_app_id": "",
        "wechat_app_secret": "",
        "wechat_token": "",
    }),
    RouteCase("GET", "/wechat/<uuid:app_id>", "/wechat/{app_id}", expected_codes=(HttpCode.FAIL,)),
    RouteCase("POST", "/wechat/<uuid:app_id>", "/wechat/{app_id}", content="text", expected_codes=None),
]


def _expand(value: Any, context: dict[str, Any]) -> Any:
    if isinstance(value, str):
        return value.format(**context)
    if isinstance(value, dict):
        return {key: _expand(item, context) for key, item in value.items()}
    if isinstance(value, list):
        return [_expand(item, context) for item in value]
    return value


def _assert_success(resp, endpoint: str) -> None:
    assert resp.status_code == 200, f"{endpoint} returned HTTP {resp.status_code}: {resp.data[:300]!r}"
    assert resp.is_json, f"{endpoint} did not return JSON: {resp.content_type}"
    assert resp.json["code"] == HttpCode.SUCCESS, f"{endpoint} failed: {resp.json}"


@pytest.fixture()
def router_context(client, test_account):
    suffix = uuid4().hex[:8]
    context: dict[str, Any] = {
        "suffix": suffix,
        "account_email": test_account.email,
        "account_password": os.getenv("DEFAULT_ACCOUNT_PASSWORD", "xxx@163.com"),
        "missing_id": str(uuid4()),
        "missing_segment_id": str(uuid4()),
        "missing_message_id": str(uuid4()),
        "task_id": str(uuid4()),
        "openapi_schema_json": json.dumps(OPENAPI_SCHEMA),
    }

    app_resp = client.post("/apps", json={
        "name": f"router_context_app_{suffix}",
        "icon": "https://img.aiflowline.cn/blog/20260806162348866.png?imageSlim",
        "description": "router context app",
    })
    _assert_success(app_resp, "create app")
    context["app_id"] = app_resp.json["data"]["id"]

    dataset_resp = client.post("/datasets", json={
        "name": f"router_context_dataset_{suffix}",
        "icon": "https://img.aiflowline.cn/blog/20260806162348866.png?imageSlim",
        "description": "router context dataset",
    })
    _assert_success(dataset_resp, "create dataset")
    datasets_resp = client.get("/datasets", query_string={"search_word": f"router_context_dataset_{suffix}"})
    _assert_success(datasets_resp, "list dataset")
    context["dataset_id"] = datasets_resp.json["data"]["list"][0]["id"]

    workflow_resp = client.post("/workflows", json={
        "name": f"router_context_workflow_{suffix}",
        "tool_call_name": f"router_context_workflow_{suffix}",
        "icon": "https://img.aiflowline.cn/blog/20260806162348866.png?imageSlim",
        "description": "router context workflow",
    })
    _assert_success(workflow_resp, "create workflow")
    context["workflow_id"] = workflow_resp.json["data"]["id"]

    provider_resp = client.post("/api-tools", json={
        "name": f"rt_context_provider_{suffix}",
        "icon": "https://img.aiflowline.cn/blog/20260806162348866.png?imageSlim",
        "openapi_schema": context["openapi_schema_json"],
        "headers": [],
    })
    _assert_success(provider_resp, "create api tool provider")
    providers_resp = client.get("/api-tools", query_string={"search_word": f"rt_context_provider_{suffix}"})
    _assert_success(providers_resp, "list api tool provider")
    context["provider_id"] = providers_resp.json["data"]["list"][0]["id"]

    api_key_resp = client.post("/openapi/api-keys", json={"is_active": True, "remark": "router context key"})
    _assert_success(api_key_resp, "create api key")
    api_keys_resp = client.get("/openapi/api-keys", query_string={"current_page": 1, "page_size": 1})
    _assert_success(api_keys_resp, "list api keys")
    context["api_key_id"] = api_keys_resp.json["data"]["list"][0]["id"]
    context["api_key"] = api_keys_resp.json["data"]["list"][0]["api_key"]

    return context


def test_router_contract_matrix_matches_registered_rules(app):
    registered = {
        (method, rule.rule)
        for rule in app.url_map.iter_rules()
        if rule.endpoint != "static"
        for method in rule.methods - {"HEAD", "OPTIONS"}
    }
    covered = {(case.method, case.rule) for case in ROUTE_CASES}

    assert registered - covered == set()
    assert covered - registered == set()


@pytest.mark.parametrize("case", ROUTE_CASES, ids=lambda case: f"{case.method} {case.rule}")
def test_router_case_returns_expected_api_contract(client, router_context, case: RouteCase):
    path = _expand(case.path, router_context)
    kwargs: dict[str, Any] = {}

    if case.query is not None:
        kwargs["query_string"] = _expand(case.query, router_context)
    if case.json is not None:
        kwargs["json"] = _expand(case.json, router_context)
    if case.auth == "api_key":
        kwargs["headers"] = {"Authorization": f"Bearer {router_context['api_key']}"}

    resp = client.open(path, method=case.method, **kwargs)
    assert resp.status_code < 500, f"{case.method} {path} returned HTTP {resp.status_code}: {resp.data[:300]!r}"

    if case.content == "binary":
        assert resp.status_code == 200
        assert not resp.data.lstrip().lower().startswith(b"<!doctype html")
        assert resp.content_type.startswith(("image/", "application/octet-stream"))
        return

    if case.content == "stream":
        assert resp.status_code == 200
        assert resp.content_type.startswith("text/event-stream")
        return

    if case.content == "text":
        assert resp.status_code == 200
        assert not resp.data.lstrip().lower().startswith(b"<!doctype html")
        return

    assert resp.is_json, f"{case.method} {path} returned non-JSON {resp.content_type}: {resp.data[:300]!r}"
    payload = resp.get_json()
    assert set(payload) >= {"code", "message", "data"}

    if case.expected_codes is not None:
        assert payload["code"] in case.expected_codes, f"{case.method} {path} returned unexpected payload: {payload}"
