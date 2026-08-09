#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/5/2 
@Author : wzy
@File   : upload_file_service
"""
from dataclasses import dataclass

from injector import inject

from internal.model import UploadFile
from internal.service.base_service import BaseService
from pkg.sqlalchemy import SQLAlchemy


@inject
@dataclass
class UploadFileService(BaseService):
    """上传文件记录服务"""
    db: SQLAlchemy

    def create_upload_file(self, **kwargs) -> UploadFile:
        """创建文件上传记录"""
        return self.create(UploadFile, **kwargs)
