#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2026/4/20
@Author : wzy
@File   : llm_node
"""
import time
from typing import Optional, Any
from uuid import UUID

from flask import Flask
from pydantic import PrivateAttr
from jinja2 import Template
from langchain_core.runnables import RunnableConfig

from internal.core.workflow.entities.node_entity import NodeResult, NodeStatus
from internal.core.workflow.entities.workflow_entity import WorkflowState
from internal.core.workflow.nodes import BaseNode
from internal.core.workflow.utils.helper import extract_variables_from_state
from internal.entity.usage_entity import UsageSource
from .llm_entity import LLMNodeData


class LLMNode(BaseNode):
    """大语言模型节点"""
    node_data: LLMNodeData
    _llm: Any = PrivateAttr(None)

    def __init__(
            self,
            *args: Any,
            flask_app: Flask,
            account_id: UUID,
            **kwargs: Any,
    ):
        """构造函数，在请求上下文内加载模型实例并挂载用量记录回调。"""
        # 1.调用父类构造函数完成数据初始化
        super().__init__(*args, **kwargs)

        # 2.导入依赖注入及语言模型服务
        from app.http.module import injector
        from internal.service import LanguageModelService

        language_model_service = injector.get(LanguageModelService)

        # 3.构建模型实例，传入用量上下文以记录该节点的token消耗（flask_app在构建期捕获，规避流式消费时上下文销毁）
        self._llm = language_model_service.load_language_model(
            self.node_data.language_model_config,
            usage_context={
                "flask_app": flask_app,
                "account_id": account_id,
                "app_id": None,
                "source": UsageSource.WORKFLOW.value,
            },
        )

    def invoke(self, state: WorkflowState, config: Optional[RunnableConfig] = None) -> WorkflowState:
        """大语言模型节点调用工具，根据输入字段+预设prompt生成对应内容后输出"""
        # 1.提取节点中的输入数据
        start_at = time.perf_counter()
        inputs_dict = extract_variables_from_state(self.node_data.inputs, state)

        # 2.使用jinja2格式模板信息
        template = Template(self.node_data.prompt)
        prompt_value = template.render(**inputs_dict)

        # 3.使用stream来代替invoke，避免接口长时间未响应超时
        content = ""
        for chunk in self._llm.stream(prompt_value):
            content += chunk.content

        # 4.提取并构建输出数据结构
        outputs = {}
        if self.node_data.outputs:
            outputs[self.node_data.outputs[0].name] = content
        else:
            outputs["output"] = content

        # 5.构建响应状态并返回
        return {
            "node_results": [
                NodeResult(
                    node_data=self.node_data,
                    status=NodeStatus.SUCCEEDED,
                    inputs=inputs_dict,
                    outputs=outputs,
                    latency=(time.perf_counter() - start_at),
                )
            ]
        }
