#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2026/9/11
@Author : wzy
@File   : usage_schema
"""
from marshmallow import Schema, fields, pre_dump
from wtforms import StringField
from wtforms.validators import Optional, AnyOf

from internal.entity.usage_entity import UsageSource
from internal.lib.helper import datetime_to_timestamp
from internal.model import UsageRecord
from pkg.paginator import PaginatorReq


class GetUsagesWithPageReq(PaginatorReq):
    """获取用量分页列表数据请求结构"""
    source = StringField("source", default="", validators=[
        Optional(),
        AnyOf(UsageSource.__members__.values(), message="用量来源格式错误")
    ])


class GetUsagesWithPageResp(Schema):
    """获取用量分页列表数据响应结构"""
    id = fields.UUID(dump_default="")
    source = fields.String(dump_default="")
    app_name = fields.String(dump_default="")
    provider_name = fields.String(dump_default="")
    model_name = fields.String(dump_default="")
    prompt_tokens = fields.Integer(dump_default=0)
    completion_tokens = fields.Integer(dump_default=0)
    total_tokens = fields.Integer(dump_default=0)
    created_at = fields.Integer(dump_default=0)

    @pre_dump
    def process_data(self, data: tuple[UsageRecord, str], **kwargs):
        usage_record, app_name = data
        return {
            "id": usage_record.id,
            "source": usage_record.source,
            "app_name": app_name if app_name else "",
            "provider_name": usage_record.provider_name,
            "model_name": usage_record.model_name,
            "prompt_tokens": usage_record.prompt_tokens,
            "completion_tokens": usage_record.completion_tokens,
            "total_tokens": usage_record.total_tokens,
            "created_at": datetime_to_timestamp(usage_record.created_at),
        }
