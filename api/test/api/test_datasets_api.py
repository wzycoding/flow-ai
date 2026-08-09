#!/usr/bin/env python
# -*- coding: utf-8 -*-
from uuid import uuid4

from pkg.response import HttpCode


def test_dataset_crud_basic_flow(client):
    dataset_name = f"pytest_dataset_{uuid4().hex[:8]}"
    payload = {
        "name": dataset_name,
        "icon": "https://img.aiflowline.cn/blog/20260806162348866.png?imageSlim",
        "description": "pytest创建的知识库",
    }

    create_resp = client.post("/datasets", json=payload)
    assert create_resp.status_code == 200
    assert create_resp.json["code"] == HttpCode.SUCCESS

    list_resp = client.get("/datasets", query_string={"search_word": dataset_name})
    assert list_resp.status_code == 200
    assert list_resp.json["code"] == HttpCode.SUCCESS
    dataset = list_resp.json["data"]["list"][0]
    dataset_id = dataset["id"]
    assert dataset["name"] == dataset_name

    get_resp = client.get(f"/datasets/{dataset_id}")
    assert get_resp.status_code == 200
    assert get_resp.json["code"] == HttpCode.SUCCESS
    assert get_resp.json["data"]["name"] == dataset_name

    delete_resp = client.post(f"/datasets/{dataset_id}/delete")
    assert delete_resp.status_code == 200
    assert delete_resp.json["code"] == HttpCode.SUCCESS
