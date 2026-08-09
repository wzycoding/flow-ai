#!/usr/bin/env python
# -*- coding: utf-8 -*-
from internal.core.tools.builtin_tools.providers.time import current_time
from pkg.response import HttpCode


def test_get_builtin_tool_categories(client):
    resp = client.get("/builtin-tools/categories")

    assert resp.status_code == 200
    assert resp.json["code"] == HttpCode.SUCCESS
    assert len(resp.json["data"]) > 0


def test_get_builtin_tools_and_schema(client):
    resp = client.get("/builtin-tools")

    assert resp.status_code == 200
    assert resp.json["code"] == HttpCode.SUCCESS
    assert any(provider["name"] == "google" for provider in resp.json["data"])


def test_get_google_serper_tool(client):
    resp = client.get("/builtin-tools/google/tools/google_serper")

    assert resp.status_code == 200
    assert resp.json["code"] == HttpCode.SUCCESS
    assert resp.json["data"]["name"] == "google_serper"
    assert resp.json["data"]["inputs"][0]["name"] == "query"


def test_current_time_tool_runs_without_external_service():
    result = current_time().invoke({})

    assert isinstance(result, str)
    assert len(result) >= 19
