#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2026/6/24
@Author  : wzy
@File    : agent_runner_service.py
"""
import structlog
from dataclasses import dataclass
from typing import Any, Generator
from uuid import UUID

from flask import current_app
from injector import inject

from internal.core.agent.agents import FunctionCallAgent, ReACTAgent
from internal.core.agent.entities.agent_entity import AgentConfig
from internal.core.agent.entities.queue_entity import QueueEvent, queue_event_name
from internal.core.language_model.entities.model_entity import ModelFeature
from internal.core.memory import TokenBufferMemory
from internal.entity.conversation_entity import InvokeFrom, MessageStatus
from internal.entity.dataset_entity import RetrievalSource
from internal.model import Account, Conversation, Message
from pkg.sqlalchemy import SQLAlchemy
from redis import Redis
from .app_config_service import AppConfigService
from .base_service import BaseService
from .conversation_service import ConversationService
from .language_model_service import LanguageModelService
from .retrieval_service import RetrievalService

logger = structlog.get_logger()


@inject
@dataclass
class AgentRunnerService(BaseService):
    """Agent执行器类"""
    db: SQLAlchemy
    redis_client: Redis
    app_config_service: AppConfigService
    language_model_service: LanguageModelService
    retrieval_service: RetrievalService
    conversation_service: ConversationService

    def prepare_agent_context(
            self,
            app_config: dict[str, Any],
            conversation: Conversation,
            account_id: UUID,
    ) -> tuple:
        """准备Agent运行所需的LLM、历史消息和工具列表"""
        logger.info("preparing_agent_context", conversation_id=str(conversation.id))

        # 1.加载大语言模型
        llm = self.language_model_service.load_language_model(
            app_config.get("model_config", {})
        )
        logger.info("llm_loaded", provider=app_config.get("model_config", {}).get("provider"), model=llm.model)

        # 2.提取短期记忆
        token_buffer_memory = TokenBufferMemory(
            db=self.db,
            conversation=conversation,
            model_instance=llm,
        )
        history = token_buffer_memory.get_history_prompt_messages(
            message_limit=app_config["dialog_round"],
        )
        logger.info("history_extracted", message_count=len(history))

        # 3.构建工具列表
        tools = self.app_config_service.get_langchain_tools_by_tools_config(
            app_config["tools"]
        )
        logger.info("tools_built", tool_count=len(tools))

        # 4.添加知识库检索工具
        if app_config["datasets"]:
            dataset_ids = [dataset["id"] for dataset in app_config["datasets"]]
            dataset_retrieval = self.retrieval_service.create_langchain_tool_from_search(
                flask_app=current_app._get_current_object(),
                dataset_ids=dataset_ids,
                account_id=account_id,
                retrival_source=RetrievalSource.APP,
                **app_config["retrieval_config"],
            )
            tools.append(dataset_retrieval)
            logger.info("dataset_retrieval_added", dataset_ids=dataset_ids)

        # 5.添加工作流工具
        if app_config["workflows"]:
            workflow_ids = [workflow["id"] for workflow in app_config["workflows"]]
            workflow_tools = self.app_config_service.get_langchain_tools_by_workflow_ids(workflow_ids)
            tools.extend(workflow_tools)
            logger.info("workflow_tools_added", workflow_ids=workflow_ids)

        logger.info("agent_context_ready", total_tool_count=len(tools))
        return llm, history, tools

    def create_agent(
            self,
            llm,
            app_config: dict[str, Any],
            tools: list,
            account_id: UUID,
            invoke_from: InvokeFrom,
    ):
        """根据LLM能力创建对应的Agent实例（FunctionCallAgent 或 ReACTAgent"""
        agent_class = FunctionCallAgent if ModelFeature.TOOL_CALL in llm.features else ReACTAgent
        logger.info(
            "creating_agent",
            agent_type=agent_class.__name__,
            invoke_from=invoke_from.value if hasattr(invoke_from, 'value') else str(invoke_from),
            tool_count=len(tools),
        )
        return agent_class(
            llm=llm,
            agent_config=AgentConfig(
                user_id=account_id,
                invoke_from=invoke_from,
                redis_client=self.redis_client,
                preset_prompt=app_config["preset_prompt"],
                enable_long_term_memory=app_config["long_term_memory"]["enable"],
                tools=tools,
                review_config=app_config["review_config"],
            ),
        )

    def run_chat_stream(
            self,
            agent,
            llm,
            query: str,
            image_urls: list,
            conversation: Conversation,
            message: Message,
            history: list,
    ) -> Generator:
        """执行Agent流式输出，构建 SSE 格式输出"""
        logger.info(
            "chat_stream_started",
            message_id=str(message.id),
            conversation_id=str(conversation.id),
        )
        accumulated_thoughts = {}
        # 接收到的都是agent_thought
        for agent_thought in agent.stream(self.build_agent_state(
            llm, query, image_urls, conversation, history,
        )):
            event_id = str(agent_thought.id)

            # 保存原始增量数据，用于 SSE 输出（前端按增量拼接）
            raw_thought = agent_thought

            # 如果不是PING事件，就累加agent_thought用于数据库持久化
            if agent_thought.event != QueueEvent.PING:
                agent_thought = self._accumulate_agent_thought(
                    accumulated_thoughts, event_id, agent_thought
                )
                # 对累加后的agent_thought进行赋值
                accumulated_thoughts[event_id] = agent_thought

            # 构建事件数据：使用原始增量（raw_thought），前端会自行拼接
            event_data = {
                **raw_thought.model_dump(include={
                    "event", "thought", "observation", "tool", "tool_input", "answer",
                    "total_token_count", "total_price", "latency",
                }),
                "id": event_id,
                "conversation_id": str(conversation.id),
                "message_id": str(message.id),
                "task_id": str(raw_thought.task_id),
            }

            yield agent_thought, event_data, queue_event_name(raw_thought.event)

        logger.info(
            "chat_stream_completed",
            message_id=str(message.id),
            thought_count=len(accumulated_thoughts),
        )

    def _accumulate_agent_thought(
            self,
            agent_thoughts: dict,
            event_id: str,
            agent_thought,
    ):
        """累加或覆盖Agent推理事件，返回处理后的thought"""
        if agent_thought.event == QueueEvent.AGENT_MESSAGE:
            if event_id not in agent_thoughts:
                return agent_thought
            return agent_thoughts[event_id].model_copy(update={
                "thought": agent_thoughts[event_id].thought + agent_thought.thought,
                # 消息相关数据
                "message": agent_thought.message,
                "message_token_count": agent_thought.message_token_count,
                "message_unit_price": agent_thought.message_unit_price,
                "message_price_unit": agent_thought.message_price_unit,
                # 答案相关数据
                "answer": agent_thoughts[event_id].answer + agent_thought.answer,
                "answer_token_count": agent_thought.answer_token_count,
                "answer_unit_price": agent_thought.answer_unit_price,
                "answer_price_unit": agent_thought.answer_price_unit,
                # Agent推理统计相关
                "total_token_count": agent_thought.total_token_count,
                "total_price": agent_thought.total_price,
                "latency": agent_thought.latency,
            })
        return agent_thought

    def build_agent_state(
            self,
            llm,
            query: str,
            image_urls: list,
            conversation: Conversation,
            history: list,
    ) -> dict:
        """构建Agent State"""
        return {
            "messages": [llm.convert_to_human_message(query, image_urls)],
            "history": history,
            "long_term_memory": conversation.summary,
        }

    def create_message(
            self,
            app_id: UUID,
            conversation_id: UUID,
            invoke_from: InvokeFrom,
            created_by: UUID,
            query: str,
            image_urls: list,
    ) -> Message:
        """创建消息记录"""
        return self.create(
            Message,
            app_id=app_id,
            conversation_id=conversation_id,
            invoke_from=invoke_from,
            created_by=created_by,
            query=query,
            image_urls=image_urls,
            status=MessageStatus.NORMAL,
        )
