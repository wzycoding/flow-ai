#!/usr/bin/env python
# -*- coding: utf-8 -*-
import io

from internal.service.cos_service import CosService
from pkg.response import HttpCode


class DummyCosClient:
    def __init__(self):
        self.uploads = []

    def put_object(self, bucket, body, key):
        self.uploads.append({"bucket": bucket, "body": body, "key": key})


def test_upload_image_uses_cos_and_returns_cos_url(client, monkeypatch):
    """图片上传应写入COS并返回COS访问地址。"""
    cos_client = DummyCosClient()
    monkeypatch.setenv("COS_BUCKET", "pytest-bucket")
    monkeypatch.setenv("COS_REGION", "ap-guangzhou")
    monkeypatch.setenv("COS_SCHEME", "https")
    monkeypatch.setenv("COS_DOMAIN", "")
    monkeypatch.setattr(CosService, "get_client", lambda self: cos_client)

    image_content = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
        b"\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02"
        b"\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDAT"
        b"\x08\xd7c\xf8\xff\xff?\x00\x05\xfe\x02\xfeA"
        b"\xe2!\xbc\x00\x00\x00\x00IEND\xaeB`\x82"
    )

    resp = client.post(
        "/upload-files/image",
        data={"file": (io.BytesIO(image_content), "dataset-icon.png")},
        content_type="multipart/form-data",
    )

    assert resp.status_code == 200
    assert resp.json["code"] == HttpCode.SUCCESS
    image_url = resp.json["data"]["image_url"]
    assert image_url.startswith("https://pytest-bucket.cos.ap-guangzhou.myqcloud.com/")
    assert len(cos_client.uploads) == 1
    assert cos_client.uploads[0]["bucket"] == "pytest-bucket"
    assert cos_client.uploads[0]["body"] == image_content


def test_upload_image_returns_failure_when_cos_unavailable(client, monkeypatch):
    """COS不可用时，上传接口应返回标准失败响应而不是写入本地文件。"""
    monkeypatch.setattr(
        CosService,
        "get_client",
        lambda self: (_ for _ in ()).throw(RuntimeError("COS unavailable")),
    )

    resp = client.post(
        "/upload-files/image",
        data={"file": (io.BytesIO(b"not-a-real-image"), "dataset-icon.png")},
        content_type="multipart/form-data",
    )

    assert resp.status_code == 200
    assert resp.json["code"] == HttpCode.FAIL
    assert resp.json["message"] == "上传文件失败，请稍后重试"
