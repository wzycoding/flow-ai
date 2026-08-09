#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2026/5/1
@Author : wzy
@File   : web_app_service
"""
import json
from dataclasses import dataclass
from typing import Generator, Any
from uuid import UUID

from injector import inject
from sqlalchemy import desc

from internal.core.agent.agents import AgentQueueManager
from internal.entity.app_entity import AppStatus
from internal.entity.conversation_entity import InvokeFrom, MessageStatus
from internal.exception import NotFoundException, ForbiddenException
from internal.model import App, Account, Conversation, Message
from internal.schema.web_app_schema import WebAppChatReq
from pkg.sqlalchemy import SQLAlchemy
from redis import Redis
from .agent_runner_service import AgentRunnerService
from .app_config_service import AppConfigService
from .base_service import BaseService
from .language_model_service import LanguageModelService


@inject
@dataclass
class WebAppService(BaseService):
    """WebApp服务"""
    db: SQLAlchemy
    redis_client: Redis
    app_config_service: AppConfigService
    agent_runner: AgentRunnerService
    language_model_service: LanguageModelService

    def get_web_app(self, token: str) -> App:
        """根据传递的token获取WebApp实例"""
        # 1.在数据库中查询token对应的应用
        app = self.db.session.query(App).filter(
            App.token == token,
        ).one_or_none()
        if not app or app.status != AppStatus.PUBLISHED:
            raise NotFoundException("该WebApp不存在或者未发布，请核实后重试")

        # 2.返回查询的应用
        return app

    def get_web_app_info(self, token: str) -> dict[str, Any]:
        """根据传递的token获取WebApp信息"""
        # 1.获取App基础信息
        app = self.get_web_app(token)

        # 2.根据App基础信息构建LLM
        app_config = self.app_config_service.get_app_config(app)
        llm = self.language_model_service.load_language_model(app_config.get("model_config", {}))

        # 3.提取信息并返回
        return {
            "id": str(app.id),
            "icon": app.icon,
            "name": app.name,
            "description": app.description,
            "app_config": {
                "opening_statement": app_config.get("opening_statement"),
                "opening_questions": app_config.get("opening_questions"),
                "suggested_after_answer": app_config.get("suggested_after_answer"),
                "features": llm.features,
                "text_to_speech": app_config.get("text_to_speech"),
                "speech_to_text": app_config.get("speech_to_text"),
            }
        }

    def web_app_chat(self, token: str, req: WebAppChatReq, account: Account) -> Generator:
        """根据传递的token凭证+请求与指定的WebApp进行对话"""
        # 1.获取WebApp应用并校验应用是否发布
        app = self.get_web_app(token)

        # 2.检测是否传递了会话id，如果传递了需要校验会话的归属信息
        if req.conversation_id.data:
            conversation = self.get(Conversation, req.conversation_id.data)
            if (
                    not conversation
                    or conversation.app_id != app.id
                    or conversation.invoke_from != InvokeFrom.WEB_APP
                    or conversation.created_by != account.id
                    or conversation.is_deleted is True
            ):
                raise ForbiddenException("该会话不存在，或者不属于当前应用/用户/调用方式")
        else:
            # 3.如果没传递conversation_id表示新会话，这时候需要创建一个会话
            conversation = self.create(Conversation, **{
                "app_id": app.id,
                "name": "New Conversation",
                "invoke_from": InvokeFrom.WEB_APP,
                "created_by": account.id,
            })

        # 4.获取校验后的运行时配置
        app_config = self.app_config_service.get_app_config(app)

        # 5.新建一条消息记录
        message = self.agent_runner.create_message(
            app_id=app.id,
            conversation_id=conversation.id,
            invoke_from=InvokeFrom.WEB_APP,
            created_by=account.id,
            query=req.query.data,
            image_urls=req.image_urls.data,
        )

        # 6.准备Agent运行上下文（LLM、历史消息、工具列表）
        llm, history, tools = self.agent_runner.prepare_agent_context(
            app_config, conversation, account.id
        )

        # 7.创建Agent实例
        agent = self.agent_runner.create_agent(
            llm, app_config, tools, account.id, InvokeFrom.WEB_APP
        )

        # 8.流式输出事件并收集推理结果
        agent_thoughts = {}
        for thought, event_data, event_name in self.agent_runner.run_chat_stream(
            agent, llm, req.query.data, req.image_urls.data,
            conversation, message, history,
        ):
            agent_thoughts[str(thought.id)] = thought
            yield f"event: {event_name}\ndata:{json.dumps(event_data)}\n\n"

        # 9.将消息以及推理过程添加到数据库
        self.agent_runner.conversation_service.save_agent_thoughts(
            account_id=account.id,
            app_id=app.id,
            app_config=app_config,
            conversation_id=conversation.id,
            message_id=message.id,
            agent_thoughts=[agent_thought for agent_thought in agent_thoughts.values()],
        )

    def stop_web_app_chat(self, token: str, task_id: UUID, account: Account):
        """根据传递的token+task_id停止与指定WebApp对话"""
        # 1.获取WebApp应用并校验应用是否发布
        self.get_web_app(token)

        # 2.调用智能体队列管理器停止特定任务
        AgentQueueManager.set_stop_flag(task_id, InvokeFrom.WEB_APP, account.id, self.redis_client)

    def get_conversations(self, token: str, is_pinned: bool, account: Account) -> list[Conversation]:
        """根据传递的token+is_pinned+account获取指定账号在该WebApp下的会话列表数据"""
        # 1.获取WebApp应用并校验应用是否发布
        app = self.get_web_app(token)

        # 2.筛选过滤并查询数据
        conversations = self.db.session.query(Conversation).filter(
            Conversation.app_id == app.id,
            Conversation.created_by == account.id,
            Conversation.invoke_from == InvokeFrom.WEB_APP,
            Conversation.is_pinned == is_pinned,
            ~Conversation.is_deleted,
        ).order_by(desc("created_at")).all()

        return conversations
