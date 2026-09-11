#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2026/9/10
@Author : wzy
@File   : usage_record
"""
from datetime import datetime

from sqlalchemy import (
    Column,
    UUID,
    String,
    Integer,
    DateTime,
    text,
    PrimaryKeyConstraint,
    Index,
)
from sqlalchemy.dialects.postgresql import JSONB

from internal.extension.database_extension import db


class UsageRecord(db.Model):
    """LLM模型用量记录，仅记录一次成功调用的真实token消耗，暂不涉及计费"""
    __tablename__ = "usage_record"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_usage_record_id"),
        Index("usage_record_account_id_idx", "account_id"),
        Index("usage_record_app_id_idx", "app_id"),
    )

    id = Column(UUID, nullable=False, server_default=text('uuid_generate_v4()'))
    account_id = Column(UUID, nullable=False)  # 消耗归属账号id
    app_id = Column(UUID, nullable=True)  # 关联应用id，辅助Agent等无应用上下文的调用为空
    source = Column(String(255), nullable=False, server_default=text("''::character varying"))  # 调用来源
    provider_name = Column(String(255), nullable=False, server_default=text("''::character varying"))  # 模型提供商名字
    model_name = Column(String(255), nullable=False, server_default=text("''::character varying"))  # 模型名字

    # token消耗，三个为核心字段，取各家服务商返回的标准usage
    prompt_tokens = Column(Integer, nullable=False, server_default=text('0'))  # 输入token数
    completion_tokens = Column(Integer, nullable=False, server_default=text('0'))  # 输出token数
    total_tokens = Column(Integer, nullable=False, server_default=text('0'))  # 总token数

    # 原始usage快照，存各家差异化的扩展字段（如缓存命中、多模态分项），未来重算用
    raw_usage = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))

    created_at = Column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP(0)'))
