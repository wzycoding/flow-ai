#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/7/15 16:17
@Author  : wzy
@File    : app_service.py
"""
import io
from dataclasses import dataclass
from typing import Any
from uuid import UUID

import requests
from injector import inject
from langchain_community.utilities.dalle_image_generator import DallEAPIWrapper
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableParallel
from internal.core.language_model.providers.tongyi.chat import Chat
from redis import Redis
from sqlalchemy import func, desc
from werkzeug.datastructures import FileStorage

from internal.core.language_model import LanguageModelManager
from internal.core.language_model.entities.model_entity import ModelParameterType
from internal.core.tools.api_tools.providers import ApiProviderManager
from internal.core.tools.builtin_tools.providers import BuiltinProviderManager
from internal.entity.ai_entity import OPTIMIZE_PROMPT_TEMPLATE
from internal.entity.app_entity import AppStatus, AppConfigType, DEFAULT_APP_CONFIG
from internal.entity.app_entity import GENERATE_ICON_PROMPT_TEMPLATE
from internal.entity.audio_entity import ALLOWED_AUDIO_VOICES
from internal.entity.workflow_entity import WorkflowStatus
from internal.exception import NotFoundException, ForbiddenException, ValidateErrorException, FailException
from internal.lib.helper import remove_fields, get_value_type, generate_random_string
from internal.model import (
    App,
    Account,
    AppConfigVersion,
    ApiTool,
    Dataset,
    AppConfig,
    AppDatasetJoin,
    Workflow,
    McpTool,
)
from internal.schema.app_schema import (
    CreateAppReq,
    GetAppsWithPageReq,
    GetPublishHistoriesWithPageReq,
)
from pkg.paginator import Paginator
from pkg.sqlalchemy import SQLAlchemy
from .app_config_service import AppConfigService
from .base_service import BaseService
from .cos_service import CosService


@inject
@dataclass
class AppService(BaseService):
    """应用服务逻辑"""
    db: SQLAlchemy
    redis_client: Redis
    cos_service: CosService
    app_config_service: AppConfigService
    api_provider_manager: ApiProviderManager
    builtin_provider_manager: BuiltinProviderManager
    language_model_manager: LanguageModelManager

    def auto_create_app(self, name: str, description: str, account_id: UUID) -> None:
        """根据传递的应用名称、描述、账号id利用AI创建一个Agent智能体"""
        # 1.创建LLM，用于生成icon提示与预设提示词
        llm = Chat(model="qwen3.7-max", temperature=0.8)

        # 2.创建DallEApiWrapper包装器
        dalle_api_wrapper = DallEAPIWrapper(model="dall-e-3", size="1024x1024")

        # 3.构建生成icon链
        generate_icon_chain = ChatPromptTemplate.from_template(
            GENERATE_ICON_PROMPT_TEMPLATE
        ) | llm | StrOutputParser() | dalle_api_wrapper.run

        # 4.生成预设prompt链
        generate_preset_prompt_chain = ChatPromptTemplate.from_messages([
            ("system", OPTIMIZE_PROMPT_TEMPLATE),
            ("human", "应用名称: {name}\n\n应用描述: {description}")
        ]) | llm | StrOutputParser()

        # 5.创建并行链同时执行两条链
        generate_app_config_chain = RunnableParallel({
            "icon": generate_icon_chain,
            "preset_prompt": generate_preset_prompt_chain,
        })
        app_config = generate_app_config_chain.invoke({"name": name, "description": description})

        # 6.将图片下载到本地后上传到腾讯云cos中
        icon_response = requests.get(app_config.get("icon"))
        if icon_response.status_code == 200:
            icon_content = icon_response.content
        else:
            raise FailException("生成应用icon图标出错")
        account = self.db.session.get(Account, account_id)
        upload_file = self.cos_service.upload_file(
            FileStorage(io.BytesIO(icon_content), filename="icon.png"),
            True,
            account,
        )
        icon = self.cos_service.get_file_url(upload_file.key)

        # 7.开启数据库自动提交上下文
        with self.db.auto_commit():
            # 8.创建应用记录并刷新数据，从而可以拿到应用id
            app = App(
                account_id=account.id,
                name=name,
                icon=icon,
                description=description,
            )
            self.db.session.add(app)
            self.db.session.flush()

            # 9.添加草稿记录
            app_config_version = AppConfigVersion(
                app_id=app.id,
                version=0,
                config_type=AppConfigType.DRAFT,
                **{
                    **DEFAULT_APP_CONFIG,
                    "preset_prompt": app_config.get("preset_prompt", ""),
                }
            )
            self.db.session.add(app_config_version)
            self.db.session.flush()

            # 10.更新应用配置id
            app.draft_app_config_id = app_config_version.id

    def create_app(self, req: CreateAppReq, account: Account) -> App:
        """创建Agent应用服务"""
        # 1.开启数据库自动提交上下文
        with self.db.auto_commit():
            # 2.创建应用记录，并刷新数据，从而可以拿到应用id
            app = App(
                account_id=account.id,
                name=req.name.data,
                icon=req.icon.data,
                description=req.description.data,
                status=AppStatus.DRAFT,
            )
            self.db.session.add(app)
            self.db.session.flush()

            # 3.添加草稿记录
            app_config_version = AppConfigVersion(
                app_id=app.id,
                version=0,
                config_type=AppConfigType.DRAFT,
                **DEFAULT_APP_CONFIG,
            )
            self.db.session.add(app_config_version)
            self.db.session.flush()

            # 4.为应用添加草稿配置id
            app.draft_app_config_id = app_config_version.id

        # 5.返回创建的应用记录
        return app

    def get_app(self, app_id: UUID, account: Account) -> App:
        """根据传递的id获取应用的基础信息"""
        # 1.查询数据库获取应用基础信息
        app = self.get(App, app_id)

        # 2.判断应用是否存在
        if not app:
            raise NotFoundException("该应用不存在，请核实后重试")

        # 3.判断当前账号是否有权限访问该应用
        if app.account_id != account.id:
            raise ForbiddenException("当前账号无权限访问该应用，请核实后尝试")

        return app

    def delete_app(self, app_id: UUID, account: Account) -> App:
        """根据传递的应用id+账号，删除指定的应用信息，目前仅删除应用基础信息即可"""
        app = self.get_app(app_id, account)
        self.delete(app)
        return app

    def update_app(self, app_id: UUID, account: Account, **kwargs) -> App:
        """根据传递的应用id+账号+信息，更新指定的应用"""
        app = self.get_app(app_id, account)
        self.update(app, **kwargs)
        return app

    def copy_app(self, app_id: UUID, account: Account) -> App:
        """根据传递的应用id，拷贝Agent相关信息并创建一个新Agent"""
        # 1.获取App+草稿配置，并校验权限
        app = self.get_app(app_id, account)
        draft_app_config = app.draft_app_config

        # 2.将数据转换为字典并剔除无用数据
        app_dict = app.__dict__.copy()
        draft_app_config_dict = draft_app_config.__dict__.copy()

        # 3.剔除无用字段
        app_remove_fields = [
            "id", "app_config_id", "draft_app_config_id", "debug_conversation_id",
            "status", "updated_at", "created_at", "_sa_instance_state",
        ]
        draft_app_config_remove_fields = [
            "id", "app_id", "version", "updated_at", "created_at", "_sa_instance_state",
        ]
        remove_fields(app_dict, app_remove_fields)
        remove_fields(draft_app_config_dict, draft_app_config_remove_fields)

        # 4.开启数据库自动提交上下文
        with self.db.auto_commit():
            # 5.创建一个新的应用记录
            new_app = App(**app_dict, status=AppStatus.DRAFT)
            self.db.session.add(new_app)
            self.db.session.flush()

            # 6.添加草稿配置
            new_draft_app_config = AppConfigVersion(
                **draft_app_config_dict,
                app_id=new_app.id,
                version=0,
            )
            self.db.session.add(new_draft_app_config)
            self.db.session.flush()

            # 7.更新应用的草稿配置id
            new_app.draft_app_config_id = new_draft_app_config.id

        # 8.返回创建好的新应用
        return new_app

    def get_apps_with_page(self, req: GetAppsWithPageReq, account: Account) -> tuple[list[App], Paginator]:
        """根据传递的分页参数获取当前登录账号下的应用分页列表数据"""
        # 1.构建分页器
        paginator = Paginator(db=self.db, req=req)

        # 2.构建筛选条件
        filters = [App.account_id == account.id]
        if req.search_word.data:
            filters.append(App.name.ilike(f"%{req.search_word.data}%"))

        # 3.执行分页操作
        apps = paginator.paginate(
            self.db.session.query(App).filter(*filters).order_by(desc("created_at"))
        )

        return apps, paginator

    def get_draft_app_config(self, app_id: UUID, account: Account) -> dict[str, Any]:
        """根据传递的应用id，获取指定的应用草稿配置信息"""
        app = self.get_app(app_id, account)
        return self.app_config_service.get_draft_app_config(app)

    def update_draft_app_config(
            self,
            app_id: UUID,
            draft_app_config: dict[str, Any],
            account: Account,
    ) -> AppConfigVersion:
        """根据传递的应用id+草稿配置修改指定应用的最新草稿"""
        # 1.获取应用信息并校验
        app = self.get_app(app_id, account)

        # 2.校验传递的草稿配置信息
        draft_app_config = self._validate_draft_app_config(draft_app_config, account)

        # 3.获取当前应用的最新草稿信息
        draft_app_config_record = app.draft_app_config
        self.update(
            draft_app_config_record,
            **draft_app_config,
        )

        return draft_app_config_record

    def publish_draft_app_config(self, app_id: UUID, account: Account) -> App:
        """根据传递的应用id+账号，发布/更新指定的应用草稿配置为运行时配置"""
        # 1.获取应用的信息以及草稿信息
        app = self.get_app(app_id, account)
        draft_app_config = self.get_draft_app_config(app_id, account)

        # 2.创建应用运行配置（在这里暂时不删除历史的运行配置）
        app_config = self.create(
            AppConfig,
            app_id=app_id,
            model_config=draft_app_config["model_config"],
            dialog_round=draft_app_config["dialog_round"],
            preset_prompt=draft_app_config["preset_prompt"],
            tools=[
                {
                    "type": tool["type"],
                    "provider_id": tool["provider"]["id"],
                    "tool_id": tool["tool"]["name"],
                    "params": tool["tool"]["params"],
                }
                for tool in draft_app_config["tools"]
            ],
            workflows=[workflow["id"] for workflow in draft_app_config["workflows"]],
            retrieval_config=draft_app_config["retrieval_config"],
            long_term_memory=draft_app_config["long_term_memory"],
            opening_statement=draft_app_config["opening_statement"],
            opening_questions=draft_app_config["opening_questions"],
            speech_to_text=draft_app_config["speech_to_text"],
            text_to_speech=draft_app_config["text_to_speech"],
            suggested_after_answer=draft_app_config["suggested_after_answer"],
            review_config=draft_app_config["review_config"],
        )

        # 3.更新应用关联的运行时配置以及状态
        self.update(app, app_config_id=app_config.id, status=AppStatus.PUBLISHED)

        # 4.先删除原有的知识库关联记录
        with self.db.auto_commit():
            self.db.session.query(AppDatasetJoin).filter(
                AppDatasetJoin.app_id == app_id,
            ).delete()

        # 5.新增新的知识库关联记录
        for dataset in draft_app_config["datasets"]:
            self.create(AppDatasetJoin, app_id=app_id, dataset_id=dataset["id"])

        # 6.获取应用草稿记录，并移除id、version、config_type、updated_at、created_at字段
        draft_app_config_copy = app.draft_app_config.__dict__.copy()
        remove_fields(
            draft_app_config_copy,
            ["id", "version", "config_type", "updated_at", "created_at", "_sa_instance_state"],
        )

        # 7.获取当前最大的发布版本
        max_version = self.db.session.query(func.coalesce(func.max(AppConfigVersion.version), 0)).filter(
            AppConfigVersion.app_id == app_id,
            AppConfigVersion.config_type == AppConfigType.PUBLISHED,
        ).scalar()

        # 8.新增发布历史配置
        self.create(
            AppConfigVersion,
            version=max_version + 1,
            config_type=AppConfigType.PUBLISHED,
            **draft_app_config_copy,
        )

        return app

    def cancel_publish_app_config(self, app_id: UUID, account: Account) -> App:
        """根据传递的应用id+账号，取消发布指定的应用配置"""
        # 1.获取应用信息并校验权限
        app = self.get_app(app_id, account)

        # 2.检测下当前应用的状态是否为已发布
        if app.status != AppStatus.PUBLISHED:
            raise FailException("当前应用未发布，请核实后重试")

        # 3.修改账号的发布状态，并清空关联配置id
        self.update(app, status=AppStatus.DRAFT, app_config_id=None)

        # 4.删除应用关联的知识库信息
        with self.db.auto_commit():
            self.db.session.query(AppDatasetJoin).filter(
                AppDatasetJoin.app_id == app_id,
            ).delete()

        return app

    def get_publish_histories_with_page(
            self,
            app_id: UUID,
            req: GetPublishHistoriesWithPageReq,
            account: Account
    ) -> tuple[list[AppConfigVersion], Paginator]:
        """根据传递的应用id+请求数据，获取指定应用的发布历史配置列表信息"""
        # 1.获取应用信息并校验权限
        self.get_app(app_id, account)

        # 2.构建分页器
        paginator = Paginator(db=self.db, req=req)

        # 3.执行分页并获取数据
        app_config_versions = paginator.paginate(
            self.db.session.query(AppConfigVersion).filter(
                AppConfigVersion.app_id == app_id,
                AppConfigVersion.config_type == AppConfigType.PUBLISHED,
            ).order_by(desc("version"))
        )

        return app_config_versions, paginator

    def fallback_history_to_draft(
            self,
            app_id: UUID,
            app_config_version_id: UUID,
            account: Account,
    ) -> AppConfigVersion:
        """根据传递的应用id、历史配置版本id、账号信息，回退特定配置到草稿"""
        # 1.校验应用权限并获取信息
        app = self.get_app(app_id, account)

        # 2.查询指定的历史版本配置id
        app_config_version = self.get(AppConfigVersion, app_config_version_id)
        if not app_config_version:
            raise NotFoundException("该历史版本配置不存在，请核实后重试")

        # 3.校验历史版本配置信息（剔除已删除的工具、知识库、工作流）
        draft_app_config_dict = app_config_version.__dict__.copy()
        remove_fields(
            draft_app_config_dict,
            ["id", "app_id", "version", "config_type", "updated_at", "created_at", "_sa_instance_state"],
        )

        # 4.校验历史版本配置信息
        draft_app_config_dict = self._validate_draft_app_config(draft_app_config_dict, account)

        # 5.更新草稿配置信息
        draft_app_config_record = app.draft_app_config
        self.update(
            draft_app_config_record,
            **draft_app_config_dict,
        )

        return draft_app_config_record

    def get_published_config(self, app_id: UUID, account: Account) -> dict[str, Any]:
        """根据传递的应用id+账号，获取应用的发布配置"""
        # 1.获取应用信息并校验权限
        app = self.get_app(app_id, account)

        # 2.构建发布配置并返回
        return {
            "web_app": {
                "token": app.token_with_default,
                "status": app.status,
            }
        }

    def regenerate_web_app_token(self, app_id: UUID, account: Account) -> str:
        """根据传递的应用id+账号，重新生成WebApp凭证标识"""
        # 1.获取应用信息并校验权限
        app = self.get_app(app_id, account)

        # 2.判断应用是否已发布
        if app.status != AppStatus.PUBLISHED:
            raise FailException("应用未发布，无法生成WebApp凭证标识")

        # 3.重新生成token并更新数据
        token = generate_random_string(16)
        self.update(app, token=token)

        return token

    # ==================== 草稿配置校验相关方法 ====================

    def _validate_draft_app_config(self, draft_app_config: dict[str, Any], account: Account) -> dict[str, Any]:
        """校验传递的应用草稿配置信息，返回校验后的数据"""
        # 1.校验上传的草稿配置中对应的字段，至少拥有一个可以更新的配置
        acceptable_fields = [
            "model_config", "dialog_round", "preset_prompt",
            "tools", "workflows", "datasets", "retrieval_config",
            "long_term_memory", "opening_statement", "opening_questions",
            "speech_to_text", "text_to_speech", "suggested_after_answer", "review_config",
        ]

        # 2.判断传递的草稿配置是否在可接受字段内
        if (
                not draft_app_config
                or not isinstance(draft_app_config, dict)
                or set(draft_app_config.keys()) - set(acceptable_fields)
        ):
            raise ValidateErrorException("草稿配置字段出错，请核实后重试")

        # 3.按字段分发校验
        validators = {
            "model_config": self._validate_model_config,
            "dialog_round": self._validate_dialog_round,
            "preset_prompt": self._validate_preset_prompt,
            "tools": self._validate_tools,
            "workflows": self._validate_workflows,
            "datasets": self._validate_datasets,
            "retrieval_config": self._validate_retrieval_config,
            "long_term_memory": self._validate_long_term_memory,
            "opening_statement": self._validate_opening_statement,
            "opening_questions": self._validate_opening_questions,
            "speech_to_text": self._validate_speech_to_text,
            "text_to_speech": self._validate_text_to_speech,
            "suggested_after_answer": self._validate_suggested_after_answer,
            "review_config": self._validate_review_config,
        }

        for field, validator in validators.items():
            if field in draft_app_config:
                validator(draft_app_config, account)

        return draft_app_config

    def _validate_model_config(self, draft_app_config: dict[str, Any], account: Account) -> None:
        """校验模型配置，provider/model使用严格校验，parameters使用宽松校验"""
        model_config = draft_app_config["model_config"]
        if not isinstance(model_config, dict):
            raise ValidateErrorException("模型配置格式错误，请核实后重试")

        # 校验model_config键信息
        if set(model_config.keys()) != {"provider", "model", "parameters"}:
            raise ValidateErrorException("模型键配置格式错误，请核实后重试")

        # 校验模型提供者
        if not model_config["provider"] or not isinstance(model_config["provider"], str):
            raise ValidateErrorException("模型服务提供商类型必须为字符串")
        provider = self.language_model_manager.get_provider(model_config["provider"])
        if not provider:
            raise ValidateErrorException("该模型服务提供商不存在，请核实后重试")

        # 校验模型名称
        if not model_config["model"] or not isinstance(model_config["model"], str):
            raise ValidateErrorException("模型名字必须是否字符串")
        model_entity = provider.get_model_entity(model_config["model"])
        if not model_entity:
            raise ValidateErrorException("该服务提供商下不存在该模型，请核实后重试")

        # 校验并修正模型参数
        model_config["parameters"] = self._validate_model_parameters(
            model_config["parameters"], model_entity
        )
        draft_app_config["model_config"] = model_config

    def _validate_model_parameters(self, parameters: dict, model_entity) -> dict:
        """校验模型参数，返回校验后的参数字典"""
        result = {}
        for parameter in model_entity.parameters:
            parameter_value = parameters.get(parameter.name, parameter.default)
            result[parameter.name] = self._validate_single_parameter(parameter_value, parameter)
        return result

    def _validate_single_parameter(self, value: Any, parameter) -> Any:
        """校验单个模型参数，返回校验后的值，不合法时回退到默认值"""
        # 必填校验：值不允许为None
        if parameter.required and value is None:
            return parameter.default

        # 类型校验：非空时需要校验类型
        if value is not None and get_value_type(value) != parameter.type.value:
            return parameter.default

        # options校验：值必须在options中
        if parameter.options and value not in parameter.options:
            return parameter.default

        # 数值范围校验：int/float类型的min/max
        if parameter.type in [ModelParameterType.INT, ModelParameterType.FLOAT] and value is not None:
            if (parameter.min and value < parameter.min) or (parameter.max and value > parameter.max):
                return parameter.default

        return value

    def _validate_dialog_round(self, draft_app_config: dict[str, Any], account: Account) -> None:
        """校验上下文轮数"""
        dialog_round = draft_app_config["dialog_round"]
        if not isinstance(dialog_round, int) or not (0 <= dialog_round <= 100):
            raise ValidateErrorException("携带上下文轮数范围为0-100")

    def _validate_preset_prompt(self, draft_app_config: dict[str, Any], account: Account) -> None:
        """校验预设提示词"""
        preset_prompt = draft_app_config["preset_prompt"]
        if not isinstance(preset_prompt, str) or len(preset_prompt) > 2000:
            raise ValidateErrorException("人设与回复逻辑必须是字符串，长度在0-2000个字符")

    def _validate_tools(self, draft_app_config: dict[str, Any], account: Account) -> None:
        """校验工具列表，过滤不存在的工具并检测重复"""
        tools = draft_app_config["tools"]
        validate_tools = []

        if not isinstance(tools, list):
            raise ValidateErrorException("工具列表必须是列表型数据")
        if len(tools) > 5:
            raise ValidateErrorException("Agent绑定的工具数不能超过5")

        for tool in tools:
            # 校验工具基本结构
            if not tool or not isinstance(tool, dict):
                raise ValidateErrorException("绑定插件工具参数出错")
            if set(tool.keys()) != {"type", "provider_id", "tool_id", "params"}:
                raise ValidateErrorException("绑定插件工具参数出错")
            if tool["type"] not in ["builtin_tool", "api_tool", "mcp_tool"]:
                raise ValidateErrorException("绑定插件工具参数出错")
            if (
                    not tool["provider_id"]
                    or not tool["tool_id"]
                    or not isinstance(tool["provider_id"], str)
                    or not isinstance(tool["tool_id"], str)
            ):
                raise ValidateErrorException("插件提供者或者插件标识参数出错")
            if not isinstance(tool["params"], dict):
                raise ValidateErrorException("插件自定义参数格式错误")

            # 校验工具是否存在，不存在则跳过
            if tool["type"] == "builtin_tool":
                builtin_tool = self.builtin_provider_manager.get_tool(tool["provider_id"], tool["tool_id"])
                if not builtin_tool:
                    continue
            elif tool["type"] == "api_tool":
                api_tool = self.db.session.query(ApiTool).filter(
                    ApiTool.provider_id == tool["provider_id"],
                    ApiTool.name == tool["tool_id"],
                    ApiTool.account_id == account.id,
                ).one_or_none()
                if not api_tool:
                    continue
            else:
                mcp_tool = self.db.session.query(McpTool).filter(
                    McpTool.provider_id == tool["provider_id"],
                    McpTool.name == tool["tool_id"],
                    McpTool.account_id == account.id,
                ).one_or_none()
                if not mcp_tool:
                    continue

            validate_tools.append(tool)

        # 校验绑定的工具是否重复
        check_tools = [f"{tool['provider_id']}_{tool['tool_id']}" for tool in validate_tools]
        if len(set(check_tools)) != len(validate_tools):
            raise ValidateErrorException("绑定插件存在重复")

        draft_app_config["tools"] = validate_tools

    def _validate_workflows(self, draft_app_config: dict[str, Any], account: Account) -> None:
        """校验工作流列表，过滤无权限或未发布的工作流"""
        workflows = draft_app_config["workflows"]

        if not isinstance(workflows, list):
            raise ValidateErrorException("绑定工作流列表参数格式错误")
        if len(workflows) > 5:
            raise ValidateErrorException("Agent绑定的工作流数量不能超过5个")

        for workflow_id in workflows:
            try:
                UUID(workflow_id)
            except Exception as _:
                raise ValidateErrorException("工作流参数必须是UUID")

        if len(set(workflows)) != len(workflows):
            raise ValidateErrorException("绑定工作流存在重复")

        # 校验权限，剔除不属于当前账号或未发布的工作流
        workflow_records = self.db.session.query(Workflow).filter(
            Workflow.id.in_(workflows),
            Workflow.account_id == account.id,
            Workflow.status == WorkflowStatus.PUBLISHED,
        ).all()
        workflow_sets = set([str(workflow_record.id) for workflow_record in workflow_records])
        draft_app_config["workflows"] = [workflow_id for workflow_id in workflows if workflow_id in workflow_sets]

    def _validate_datasets(self, draft_app_config: dict[str, Any], account: Account) -> None:
        """校验知识库列表，过滤无权限的知识库"""
        datasets = draft_app_config["datasets"]

        if not isinstance(datasets, list):
            raise ValidateErrorException("绑定知识库列表参数格式错误")
        if len(datasets) > 5:
            raise ValidateErrorException("Agent绑定的知识库数量不能超过5个")

        for dataset_id in datasets:
            try:
                UUID(dataset_id)
            except Exception as e:
                raise ValidateErrorException("知识库列表参数必须是UUID")

        if len(set(datasets)) != len(datasets):
            raise ValidateErrorException("绑定知识库存在重复")

        # 校验权限，剔除不属于当前账号的知识库
        dataset_records = self.db.session.query(Dataset).filter(
            Dataset.id.in_(datasets),
            Dataset.account_id == account.id,
        ).all()
        dataset_sets = set([str(dataset_record.id) for dataset_record in dataset_records])
        draft_app_config["datasets"] = [dataset_id for dataset_id in datasets if dataset_id in dataset_sets]

    def _validate_retrieval_config(self, draft_app_config: dict[str, Any], account: Account) -> None:
        """校验检索配置"""
        retrieval_config = draft_app_config["retrieval_config"]

        if not retrieval_config or not isinstance(retrieval_config, dict):
            raise ValidateErrorException("检索配置格式错误")
        if set(retrieval_config.keys()) != {"retrieval_strategy", "k", "score"}:
            raise ValidateErrorException("检索配置格式错误")
        if retrieval_config["retrieval_strategy"] not in ["semantic", "full_text", "hybrid"]:
            raise ValidateErrorException("检测策略格式错误")
        if not isinstance(retrieval_config["k"], int) or not (0 <= retrieval_config["k"] <= 10):
            raise ValidateErrorException("最大召回数量范围为0-10")
        if not isinstance(retrieval_config["score"], float) or not (0 <= retrieval_config["score"] <= 1):
            raise ValidateErrorException("最小匹配范围为0-1")

    def _validate_long_term_memory(self, draft_app_config: dict[str, Any], account: Account) -> None:
        """校验长期记忆配置"""
        long_term_memory = draft_app_config["long_term_memory"]

        if not long_term_memory or not isinstance(long_term_memory, dict):
            raise ValidateErrorException("长期记忆设置格式错误")
        if (
                set(long_term_memory.keys()) != {"enable"}
                or not isinstance(long_term_memory["enable"], bool)
        ):
            raise ValidateErrorException("长期记忆设置格式错误")

    def _validate_opening_statement(self, draft_app_config: dict[str, Any], account: Account) -> None:
        """校验对话开场白"""
        opening_statement = draft_app_config["opening_statement"]
        if not isinstance(opening_statement, str) or len(opening_statement) > 2000:
            raise ValidateErrorException("对话开场白的长度范围是0-2000")

    def _validate_opening_questions(self, draft_app_config: dict[str, Any], account: Account) -> None:
        """校验开场建议问题列表"""
        opening_questions = draft_app_config["opening_questions"]

        if not isinstance(opening_questions, list) or len(opening_questions) > 3:
            raise ValidateErrorException("开场建议问题不能超过3个")
        for opening_question in opening_questions:
            if not isinstance(opening_question, str):
                raise ValidateErrorException("开场建议问题必须是字符串")

    def _validate_speech_to_text(self, draft_app_config: dict[str, Any], account: Account) -> None:
        """校验语音转文本配置"""
        speech_to_text = draft_app_config["speech_to_text"]

        if not speech_to_text or not isinstance(speech_to_text, dict):
            raise ValidateErrorException("语音转文本设置格式错误")
        if (
                set(speech_to_text.keys()) != {"enable"}
                or not isinstance(speech_to_text["enable"], bool)
        ):
            raise ValidateErrorException("语音转文本设置格式错误")

    def _validate_text_to_speech(self, draft_app_config: dict[str, Any], account: Account) -> None:
        """校验文本转语音配置"""
        text_to_speech = draft_app_config["text_to_speech"]

        if not isinstance(text_to_speech, dict):
            raise ValidateErrorException("文本转语音设置格式错误")
        if (
                set(text_to_speech.keys()) != {"enable", "voice", "auto_play"}
                or not isinstance(text_to_speech["enable"], bool)
                or text_to_speech["voice"] not in ALLOWED_AUDIO_VOICES
                or not isinstance(text_to_speech["auto_play"], bool)
        ):
            raise ValidateErrorException("文本转语音设置格式错误")

    def _validate_suggested_after_answer(self, draft_app_config: dict[str, Any], account: Account) -> None:
        """校验回答后生成建议问题配置"""
        suggested_after_answer = draft_app_config["suggested_after_answer"]

        if not suggested_after_answer or not isinstance(suggested_after_answer, dict):
            raise ValidateErrorException("回答后建议问题设置格式错误")
        if (
                set(suggested_after_answer.keys()) != {"enable"}
                or not isinstance(suggested_after_answer["enable"], bool)
        ):
            raise ValidateErrorException("回答后建议问题设置格式错误")

    def _validate_review_config(self, draft_app_config: dict[str, Any], account: Account) -> None:
        """校验审核配置"""
        review_config = draft_app_config["review_config"]

        # 校验基本结构
        if not review_config or not isinstance(review_config, dict):
            raise ValidateErrorException("审核配置格式错误")
        if set(review_config.keys()) != {"enable", "keywords", "inputs_config", "outputs_config"}:
            raise ValidateErrorException("审核配置格式错误")

        # 校验enable
        if not isinstance(review_config["enable"], bool):
            raise ValidateErrorException("review.enable格式错误")

        # 校验keywords
        if (
                not isinstance(review_config["keywords"], list)
                or (review_config["enable"] and len(review_config["keywords"]) == 0)
                or len(review_config["keywords"]) > 100
        ):
            raise ValidateErrorException("review.keywords非空且不能超过100个关键词")
        for keyword in review_config["keywords"]:
            if not isinstance(keyword, str):
                raise ValidateErrorException("review.keywords敏感词必须是字符串")

        # 校验inputs_config
        if (
                not review_config["inputs_config"]
                or not isinstance(review_config["inputs_config"], dict)
                or set(review_config["inputs_config"].keys()) != {"enable", "preset_response"}
                or not isinstance(review_config["inputs_config"]["enable"], bool)
                or not isinstance(review_config["inputs_config"]["preset_response"], str)
        ):
            raise ValidateErrorException("review.inputs_config必须是一个字典")

        # 校验outputs_config
        if (
                not review_config["outputs_config"]
                or not isinstance(review_config["outputs_config"], dict)
                or set(review_config["outputs_config"].keys()) != {"enable"}
                or not isinstance(review_config["outputs_config"]["enable"], bool)
        ):
            raise ValidateErrorException("review.outputs_config格式错误")

        # 开启审核时，输入审核和输出审核至少需要开启一项
        if review_config["enable"]:
            if (
                    review_config["inputs_config"]["enable"] is False
                    and review_config["outputs_config"]["enable"] is False
            ):
                raise ValidateErrorException("输入审核和输出审核至少需要开启一项")

            if (
                    review_config["inputs_config"]["enable"]
                    and review_config["inputs_config"]["preset_response"].strip() == ""
            ):
                raise ValidateErrorException("输入审核预设响应不能为空")
