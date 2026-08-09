#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

from pkg.response import HttpCode


def test_password_login_with_seeded_account(anonymous_client, test_account):
    resp = anonymous_client.post("/auth/password-login", json={
        "email": os.getenv("DEFAULT_ACCOUNT_EMAIL", "xxx@163.com"),
        "password": os.getenv("DEFAULT_ACCOUNT_PASSWORD", "xxx@163.com"),
    })

    assert resp.status_code == 200
    assert resp.json["code"] == HttpCode.SUCCESS
    assert resp.json["data"]["access_token"]


def test_get_current_account(client):
    resp = client.get("/account")

    assert resp.status_code == 200
    assert resp.json["code"] == HttpCode.SUCCESS
    assert resp.json["data"]["email"] == os.getenv("DEFAULT_ACCOUNT_EMAIL", "xxx@163.com")
