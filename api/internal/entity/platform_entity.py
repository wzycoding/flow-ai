#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2026/5/15 
@Author : wzy
@File   : platform_entity
"""
from enum import Enum


class WechatConfigStatus(str, Enum):
    """微信配置状态"""
    CONFIGURED = "configured"  # 已配置
    UNCONFIGURED = "unconfigured"  # 未配置
