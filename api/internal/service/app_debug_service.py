#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2026/6/24
@Author  : wzy
@File    : app_debug_service.py
"""
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Generator
from uuid import UUID

from injector import inject
from sqlalchemy import desc
from sqlalchemy.orm import joinedload

from internal.core.agent.agents import AgentQueueManager
from internal.entity.conversation_entity import InvokeFrom, MessageStatus
from internal.exception import FailException
from internal.model import App, Account, Conversation, Message
from internal.schema.app_schema import (
    DebugChatReq,
    GetDebugConversationMessagesWithPageReq,
)
from pkg.paginator import Paginator
from pkg.sqlalchemy import SQLAlchemy
from redis import Redis
from .agent_runner_service import AgentRunnerService
from .app_service import AppService
from .base_service import BaseService
from .app_config_service import AppConfigService


@inject
@dataclass
class AppDebugService(BaseService):
    """应用调试会话服务"""
    db: SQLAlchemy
    redis_client: Redis
    app_service: AppService
    app_config_service: AppConfigService
    agent_runner: AgentRunnerService

    def get_debug_conversation_summary(self, app_id: UUID, account: Account) -> str:
        """根据传递的应用id+账号获取指定应用的调试会话长期记忆"""
        # 1.获取应用信息并校验权限
        app = self.app_service.get_app(app_id, account)

        # 2.获取应用的草稿配置，并校验长期记忆是否启用
        draft_app_config = self.app_config_service.get_draft_app_config(app)
        if draft_app_config["long_term_memory"]["enable"] is False:
            raise FailException("该应用并未开启长期记忆，无法获取")

        return app.debug_conversation.summary

    def update_debug_conversation_summary(self, app_id: UUID, summary: str, account: Account) -> Conversation:
        """根据传递的应用id+总结更新指定应用的调试长期记忆"""
        # 1.获取应用信息并校验权限
        app = self.app_service.get_app(app_id, account)

        # 2.获取应用的草稿配置，并校验长期记忆是否启用
        draft_app_config = self.app_config_service.get_draft_app_config(app)
        if draft_app_config["long_term_memory"]["enable"] is False:
            raise FailException("该应用并未开启长期记忆，无法获取")

        # 3.更新应用长期记忆
        debug_conversation = app.debug_conversation
        self.update(debug_conversation, summary=summary)

        return debug_conversation

    def delete_debug_conversation(self, app_id: UUID, account: Account) -> App:
        """根据传递的应用id，删除指定的应用调试会话"""
        # 1.获取应用信息并校验权限
        app = self.app_service.get_app(app_id, account)

        # 2.判断是否存在debug_conversation_id这个数据，如果不存在表示没有会话，无需执行任何操作
        if not app.debug_conversation_id:
            return app

        # 3.否则将debug_conversation_id的值重置为None
        self.update(app, debug_conversation_id=None)

        return app

    def debug_chat(self, app_id: UUID, req: DebugChatReq, account: Account) -> Generator:
        """根据传递的应用id+提问query向特定的应用发起会话调试"""
        # 1.获取应用信息和草稿配置
        app = self.app_service.get_app(app_id, account)
        draft_app_config = self.app_config_service.get_draft_app_config(app)
        debug_conversation = app.debug_conversation

        # 2.创建消息记录
        message = self.agent_runner.create_message(
            app_id=app_id,
            conversation_id=debug_conversation.id,
            invoke_from=InvokeFrom.DEBUGGER,
            created_by=account.id,
            query=req.query.data,
            image_urls=req.image_urls.data,
        )

        # 3.准备Agent运行上下文（LLM、历史消息、工具列表）
        llm, history, tools = self.agent_runner.prepare_agent_context(
            draft_app_config, debug_conversation, account.id
        )

        # 4.创建Agent实例
        agent = self.agent_runner.create_agent(
            llm, draft_app_config, tools, account.id, InvokeFrom.DEBUGGER
        )

        # 5.流式输出事件并收集推理结果
        agent_thoughts = {}
        for thought, event_data, event_name in self.agent_runner.run_chat_stream(
            agent, llm, req.query.data, req.image_urls.data,
            debug_conversation, message, history,
        ):
            agent_thoughts[str(thought.id)] = thought
            yield f"event: {event_name}\ndata:{json.dumps(event_data, ensure_ascii=False)}\n\n"

        # 6.持久化推理结果
        self.agent_runner.conversation_service.save_agent_thoughts(
            account_id=account.id,
            app_id=app.id,
            app_config=draft_app_config,
            conversation_id=debug_conversation.id,
            message_id=message.id,
            agent_thoughts=list(agent_thoughts.values()),
        )

    def stop_debug_chat(self, app_id: UUID, task_id: UUID, account: Account) -> None:
        """根据传递的应用id+任务id+账号，停止某个应用的调试会话，中断流式事件"""
        # 1.获取应用信息并校验权限
        self.app_service.get_app(app_id, account)

        # 2.调用智能体队列管理器停止特定任务
        AgentQueueManager.set_stop_flag(task_id, InvokeFrom.DEBUGGER, account.id, self.redis_client)

    def get_debug_conversation_messages_with_page(
            self,
            app_id: UUID,
            req: GetDebugConversationMessagesWithPageReq,
            account: Account
    ) -> tuple[list[Message], Paginator]:
        """根据传递的应用id+请求数据，获取调试会话消息列表分页数据"""
        # 1.获取应用信息并校验权限
        app = self.app_service.get_app(app_id, account)

        # 2.获取应用的调试会话
        debug_conversation = app.debug_conversation

        # 3.构建分页器并构建游标条件
        paginator = Paginator(db=self.db, req=req)
        filters = []
        if req.created_at.data:
            # 4.将时间戳转换成DateTime
            created_at_datetime = datetime.fromtimestamp(req.created_at.data)
            filters.append(Message.created_at <= created_at_datetime)

        # 5.执行分页并查询数据
        messages = paginator.paginate(
            self.db.session.query(Message).options(joinedload(Message.agent_thoughts)).filter(
                Message.conversation_id == debug_conversation.id,
                Message.status.in_([MessageStatus.STOP, MessageStatus.NORMAL]),
                Message.answer != "",
                *filters,
            ).order_by(desc("created_at"))
        )

        return messages, paginator
