#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/3/20 
@Author : wzy
@File   : base_service
"""
from typing import Any, Optional

from internal.exception import FailException
from pkg.sqlalchemy import SQLAlchemy


class BaseService:
    """基础服务，完善数据库的基础增删改查功能， 简化代码"""
    db: SQLAlchemy

    def create(self, model: Any, **kwargs) -> Any:
        """根据传递的模型类+键值对参数信息创建数据库记录"""
        with self.db.auto_commit():
            model_instance = model(**kwargs)
            self.db.session.add(model_instance)
        return model_instance

    def delete(self, model_instance: Any) -> Any:
        """根据传递的模型实例删除数据库记录"""
        with self.db.auto_commit():
            self.db.session.delete(model_instance)
        return model_instance

    def update(self, model_instance: Any, **kwargs) -> Any:
        """根据传递的模型实例+键值对参数信息更新数据库记录"""
        with self.db.auto_commit():
            # detached object 安全处理
            model_instance = self.db.session.merge(model_instance)

            for field, value in kwargs.items():
                if hasattr(model_instance, field):
                    # 设置更新的字段值
                    setattr(model_instance, field, value)
                else:
                    raise FailException("更新数据失败")
        return model_instance

    def get(self, model: Any, primary_key: Any) -> Optional[Any]:
        """根据传递的模型类+主键id获取唯一数据"""
        return self.db.session.get(model, primary_key)
