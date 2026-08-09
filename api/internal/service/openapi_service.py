#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2026/4/16
@Author : wzy
@File   : openapi_service
"""
import json
from dataclasses import dataclass
from typing import Generator

from injector import inject

from internal.core.agent.entities.queue_entity import QueueEvent, queue_event_name
from internal.entity.app_entity import AppStatus
from internal.entity.conversation_entity import InvokeFrom, MessageStatus
from internal.exception import NotFoundException, ForbiddenException
from internal.model import Account, EndUser, Conversation, Message
from internal.schema.openapi_schema import OpenAPIChatReq
from pkg.response import Response
from pkg.sqlalchemy import SQLAlchemy
from .agent_runner_service import AgentRunnerService
from .app_config_service import AppConfigService
from .app_service import AppService
from .base_service import BaseService


@inject
@dataclass
class OpenAPIService(BaseService):
    """开放API服务"""
    db: SQLAlchemy
    app_service: AppService
    app_config_service: AppConfigService
    agent_runner: AgentRunnerService

    def chat(self, req: OpenAPIChatReq, account: Account):
        """根据传递的请求+账号信息发起聊天对话，返回数据为块内容或者生成器"""
        # 1.判断当前应用是否属于当前账号
        app = self.app_service.get_app(req.app_id.data, account)

        # 2.判断当前应用是否已发布
        if app.status != AppStatus.PUBLISHED:
            raise NotFoundException("该应用不存在或未发布，请核实后重试")

        # 3.判断是否传递了终端用户id，如果传递了则检测终端用户关联的应用
        if req.end_user_id.data:
            end_user = self.get(EndUser, req.end_user_id.data)
            if not end_user or end_user.app_id != app.id:
                raise ForbiddenException("当前账号不存在或不属于该应用，请核实后重试")
        else:
            # 4.如果不存在则创建一个终端用户
            end_user = self.create(
                EndUser,
                **{"tenant_id": account.id, "app_id": app.id},
            )

        # 5.检测是否传递了会话id，如果传递了需要检测会话的归属信息
        if req.conversation_id.data:
            conversation = self.get(Conversation, req.conversation_id.data)
            if (
                    not conversation
                    or conversation.app_id != app.id
                    or conversation.invoke_from != InvokeFrom.SERVICE_API
                    or conversation.created_by != end_user.id
            ):
                raise ForbiddenException("该会话不存在，或者不属于该应用/终端用户/调用方式")
        else:
            # 6.如果不存在则创建会话信息
            conversation = self.create(Conversation, **{
                "app_id": app.id,
                "name": "New Conversation",
                "invoke_from": InvokeFrom.SERVICE_API,
                "created_by": end_user.id,
            })

        # 7.获取校验后的运行时配置
        app_config = self.app_config_service.get_app_config(app)

        # 8.新建一条消息记录
        message = self.agent_runner.create_message(
            app_id=app.id,
            conversation_id=conversation.id,
            invoke_from=InvokeFrom.SERVICE_API,
            created_by=end_user.id,
            query=req.query.data,
            image_urls=req.image_urls.data,
        )

        # 9.准备Agent运行上下文（LLM、历史消息、工具列表）
        llm, history, tools = self.agent_runner.prepare_agent_context(
            app_config, conversation, account.id
        )

        # 10.创建Agent实例
        agent = self.agent_runner.create_agent(
            llm, app_config, tools, account.id, InvokeFrom.DEBUGGER
        )

        # 11.根据stream类型差异执行不同的代码
        if req.stream.data is True:
            agent_thoughts_dict = {}

            def handle_stream() -> Generator:
                """流式事件处理器，在Python只要在函数内部使用了yield关键字，那么这个函数的返回值类型肯定是生成器"""
                for thought, event_data, event_name in self.agent_runner.run_chat_stream(
                    agent, llm, req.query.data, req.image_urls.data,
                    conversation, message, history,
                ):
                    event_id = str(thought.id)

                    # thought 已是累加后的完整数据，直接用于数据库持久化
                    if thought.event != QueueEvent.PING:
                        agent_thoughts_dict[event_id] = thought

                    # 构建SSE数据：使用 event_data（增量）供客户端拼接，OpenAPI额外包含end_user_id
                    data = {
                        **event_data,
                        "end_user_id": str(end_user.id),
                    }
                    yield f"event: {event_name}\ndata:{json.dumps(data)}\n\n"

                # 将消息以及推理过程添加到数据库
                self.agent_runner.conversation_service.save_agent_thoughts(
                    account_id=account.id,
                    app_id=app.id,
                    app_config=app_config,
                    conversation_id=conversation.id,
                    message_id=message.id,
                    agent_thoughts=[agent_thought for agent_thought in agent_thoughts_dict.values()],
                )

            return handle_stream()

        # 12.块内容输出
        agent_state = self.agent_runner.build_agent_state(
            llm, req.query.data, req.image_urls.data, conversation, history
        )
        agent_result = agent.invoke(agent_state)

        # 13.将消息以及推理过程添加到数据库
        self.agent_runner.conversation_service.save_agent_thoughts(
            account_id=account.id,
            app_id=app.id,
            app_config=app_config,
            conversation_id=conversation.id,
            message_id=message.id,
            agent_thoughts=agent_result.agent_thoughts,
        )

        return Response(data={
            "id": str(message.id),
            "end_user_id": str(end_user.id),
            "conversation_id": str(conversation.id),
            "query": req.query.data,
            "image_urls": req.image_urls.data,
            "answer": agent_result.answer,
            "total_token_count": 0,
            "latency": agent_result.latency,
            "agent_thoughts": [{
                "id": str(agent_thought.id),
                "event": agent_thought.event,
                "thought": agent_thought.thought,
                "observation": agent_thought.observation,
                "tool": agent_thought.tool,
                "tool_input": agent_thought.tool_input,
                "latency": agent_thought.latency,
                "created_at": 0,
            } for agent_thought in agent_result.agent_thoughts]
        })
