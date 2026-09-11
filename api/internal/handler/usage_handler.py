#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2026/9/11
@Author : wzy
@File   : usage_handler
"""
from dataclasses import dataclass

from flask import request
from flask_login import login_required, current_user
from injector import inject

from internal.schema.usage_schema import GetUsagesWithPageReq, GetUsagesWithPageResp
from internal.service import UsageService
from pkg.paginator import PageModel
from pkg.response import validate_error_json, success_json


@inject
@dataclass
class UsageHandler:
    """用量处理器"""
    usage_service: UsageService

    @login_required
    def get_usages_with_page(self):
        """获取当前登录账号的LLM用量分页列表信息"""
        # 1.提取请求并校验
        req = GetUsagesWithPageReq(request.args)
        if not req.validate():
            return validate_error_json(req.errors)

        # 2.调用服务获取数据
        usages, paginator = self.usage_service.get_usages_with_page(req, current_user)

        # 3.构建响应结构并返回
        resp = GetUsagesWithPageResp(many=True)

        return success_json(PageModel(list=resp.dump(usages), paginator=paginator))
