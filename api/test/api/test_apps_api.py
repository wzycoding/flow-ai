#!/usr/bin/env python
# -*- coding: utf-8 -*-
from uuid import uuid4

from pkg.response import HttpCode


def test_app_crud_basic_flow(client):
    app_name = f"pytest_app_{uuid4().hex[:8]}"
    payload = {
        "name": app_name,
        "icon": "https://img.aiflowline.cn/blog/20260806162348866.png?imageSlim",
        "description": "pytest创建的应用",
    }

    create_resp = client.post("/apps", json=payload)
    assert create_resp.status_code == 200
    assert create_resp.json["code"] == HttpCode.SUCCESS
    app_id = create_resp.json["data"]["id"]

    get_resp = client.get(f"/apps/{app_id}")
    assert get_resp.status_code == 200
    assert get_resp.json["code"] == HttpCode.SUCCESS
    assert get_resp.json["data"]["name"] == app_name

    list_resp = client.get("/apps", query_string={"search_word": app_name})
    assert list_resp.status_code == 200
    assert list_resp.json["code"] == HttpCode.SUCCESS
    assert list_resp.json["data"]["list"][0]["name"] == app_name

    delete_resp = client.post(f"/apps/{app_id}/delete")
    assert delete_resp.status_code == 200
    assert delete_resp.json["code"] == HttpCode.SUCCESS
