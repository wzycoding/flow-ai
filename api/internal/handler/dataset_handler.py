#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/5/1 
@Author : wzy
@File   : dataset_handler
"""
from dataclasses import dataclass
from uuid import UUID

from flask import request
from flask_login import login_required, current_user
from injector import inject

from internal.core.file_extractor import FileExtractor
from internal.schema.dataset_schema import CreateDatasetReq, GetDatasetResp, UpdateDatasetReq, GetDatasetsWithPageReq, \
    GetDatasetsWithPageResp, GetDatasetQueriesResp, HitReq
from internal.service import (
    DatasetService, JiebaService, VectorDatabaseService, EmbeddingsService
)
from pkg.paginator import PageModel
from pkg.response import validate_error_json, success_message, success_json
from pkg.sqlalchemy import SQLAlchemy


@inject
@dataclass
class DatasetHandler:
    """知识库相关接口"""
    db: SQLAlchemy
    jieba_service: JiebaService
    vector_database_service: VectorDatabaseService
    dataset_service: DatasetService
    embedding_service: EmbeddingsService
    file_extractor: FileExtractor

    @login_required
    def create_dataset(self):
        """05-01 创建知识库"""
        # 1.提取请求并校验
        req = CreateDatasetReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 2.调用服务创建知识库
        self.dataset_service.create_dataset(req, current_user)

        # 3.返回成功调用提示
        return success_message("创建知识库成功")

    @login_required
    def delete_dataset(self, dataset_id: UUID):
        """05-02 根据传递的知识库id删除知识库"""
        self.dataset_service.delete_dataset(dataset_id, current_user)
        return success_message("删除知识库成功")

    @login_required
    def update_dataset(self, dataset_id: UUID):
        """05-03 根据传递的知识库id+信息更新知识库"""
        # 1.提取请求并校验
        req = UpdateDatasetReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 2.调用服务创建知识库
        self.dataset_service.update_dataset(dataset_id, req, current_user)

        # 3.返回成功调用提示
        return success_message("更新知识库成功")

    @login_required
    def get_dataset(self, dataset_id: UUID):
        """05-04 根据传入的知识库id获取详情"""
        dataset = self.dataset_service.get_dataset(dataset_id, current_user)
        resp = GetDatasetResp()

        return success_json(resp.dump(dataset))

    @login_required
    def get_datasets_with_page(self):
        """05-05 获取分页知识库 + 搜索列表数据"""
        # 1.提取query数据并校验
        req = GetDatasetsWithPageReq(request.args)
        if not req.validate():
            return validate_error_json(req.errors)

        # 2.调用服务获取分页数据
        datasets, paginator = self.dataset_service.get_datasets_with_page(req, current_user)

        # 3.构建响应，many=True表示有多条数据
        resp = GetDatasetsWithPageResp(many=True)

        return success_json(PageModel(list=resp.dump(datasets), paginator=paginator))

    @login_required
    def hit(self, dataset_id: UUID):
        """05-06 根据拆的你的知识库id+检索参数执行召回测试"""
        # 1.提取数据并校验
        req = HitReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 2.调用服务执行检索策略
        hit_result = self.dataset_service.hit(dataset_id, req, current_user)

        return success_json(hit_result)

    @login_required
    def get_dataset_queries(self, dataset_id: UUID):
        """05-07 根据传递的知识库id获取最近的10条查询记录"""
        dataset_queries = self.dataset_service.get_dataset_queries(dataset_id, current_user)
        resp = GetDatasetQueriesResp(many=True)
        return success_json(resp.dump(dataset_queries))
