#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2026/9/11
@Author : wzy
@File   : usage_service
"""
from dataclasses import dataclass
from typing import Any

from injector import inject
from sqlalchemy import desc

from internal.model import Account, App, UsageRecord
from internal.schema.usage_schema import GetUsagesWithPageReq
from pkg.paginator import Paginator
from pkg.sqlalchemy import SQLAlchemy
from .base_service import BaseService


@inject
@dataclass
class UsageService(BaseService):
    """用量服务"""
    db: SQLAlchemy

    def get_usages_with_page(
            self,
            req: GetUsagesWithPageReq,
            account: Account,
    ) -> tuple[list[Any], Paginator]:
        """根据传递的分页请求+账号信息获取该账号的LLM用量分页列表"""
        # 1.创建分页器
        paginator = Paginator(db=self.db, req=req)

        # 2.构建筛选条件，默认仅查询当前账号的用量，存在来源时追加过滤条件
        filters = [UsageRecord.account_id == account.id]
        if req.source.data:
            filters.append(UsageRecord.source == req.source.data)

        # 3.执行分页查询并按创建时间倒序返回，db.paginate会对结果做scalars()转换，
        # 不支持连表多列查询，故只查用量记录，应用名在第4步单独补齐
        usages = paginator.paginate(
            self.db.session.query(UsageRecord)
            .filter(*filters)
            .order_by(desc("created_at"))
        )

        # 4.对当页存在应用上下文的用量批量查出应用名，组装成(用量记录, 应用名)元组供响应Schema使用，
        # 辅助Agent/后台任务等无应用id的记录以及应用已删除的记录应用名为空字符串
        app_name_map: dict[Any, str] = {}
        app_ids = {usage.app_id for usage in usages if usage.app_id}
        if app_ids:
            for app_id, app_name in self.db.session.query(App.id, App.name).filter(App.id.in_(app_ids)).all():
                app_name_map[app_id] = app_name

        return [(usage, app_name_map.get(usage.app_id, "")) for usage in usages], paginator
