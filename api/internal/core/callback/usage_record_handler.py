#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2026/9/10
@Author : wzy
@File   : usage_record_handler
"""
from typing import Any

import structlog
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult

from internal.extension.database_extension import db
from internal.model import UsageRecord

logger = structlog.get_logger()


class UsageRecordHandler(BaseCallbackHandler):
    """LLM用量记录回调，在每次模型调用结束后记录真实token消耗。

    挂载方式：在 LanguageModelService.load_language_model 构建模型实例时通过 callbacks 传入，
    因此该实例的每一轮调用（流式/非流式、agent多轮循环）都会自动触发 on_llm_end 各记录一条。
    设计原则：记账是旁路逻辑，任何异常都不得影响主对话流程，故 on_llm_end 全程静默兜底。
    """

    def __init__(
            self,
            flask_app: Any,
            account_id: Any,
            app_id: Any,
            source: str,
            provider_name: str,
            model_name: str,
    ) -> None:
        """构造用量记录回调。

        Args:
            flask_app: 捕获的 Flask app 实例(current_app._get_current_object())，
                因为流式响应消费时请求上下文可能已销毁，落库时需手动推入 app_context。
            account_id: 消耗归属账号id。
            app_id: 关联应用id，无应用上下文时可为 None。
            source: 调用来源，取值见 internal.entity.usage_entity.UsageSource。
            provider_name: 模型提供商名字。
            model_name: 模型名字。
        """
        super().__init__()
        self.flask_app = flask_app
        self.account_id = account_id
        self.app_id = app_id
        self.source = source
        self.provider_name = provider_name
        self.model_name = model_name

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """一次模型调用结束时触发，提取 usage 并落库。"""
        try:
            # 1.提取本次调用的 token 消耗，取不到或全为0（异常空响应）则跳过记录
            usage = self._extract_usage(response)
            if usage is None or (usage["prompt_tokens"] == 0 and usage["completion_tokens"] == 0):
                return

            # 2.在捕获的 app 上下文中落库（流式消费时原请求上下文可能已弹出）
            with self.flask_app.app_context():
                with db.auto_commit():
                    db.session.add(UsageRecord(
                        account_id=self.account_id,
                        app_id=self.app_id,
                        source=self.source,
                        provider_name=self.provider_name,
                        model_name=self.model_name,
                        prompt_tokens=usage["prompt_tokens"],
                        completion_tokens=usage["completion_tokens"],
                        total_tokens=usage["total_tokens"],
                        raw_usage=usage["raw_usage"],
                    ))
        except Exception as error:
            # 记账失败只记录日志，绝不向上抛出影响对话
            logger.exception("usage_record_failed", error=str(error))

    @staticmethod
    def _extract_usage(response: LLMResult) -> dict[str, Any] | None:
        """从回调结果中提取标准化的 token 消耗，返回 None 表示无可记录的用量。

        取值优先级：
        1) llm_output["token_usage"] —— 服务商原始 usage 字典，最完整，含各家扩展字段；
        2) 聚合消息的 usage_metadata —— LangChain 归一化后的 input/output/total_tokens，
           作为 token_usage 缺失时的兜底（如个别版本/非流式路径未回填 llm_output）。
        """
        # 1.优先读取服务商原始 token_usage
        token_usage = (response.llm_output or {}).get("token_usage")
        if token_usage:
            return {
                "prompt_tokens": int(token_usage.get("prompt_tokens") or 0),
                "completion_tokens": int(token_usage.get("completion_tokens") or 0),
                "total_tokens": int(token_usage.get("total_tokens") or 0),
                "raw_usage": token_usage,
            }

        # 2.兜底读取聚合消息上的 usage_metadata
        try:
            message = response.generations[0][0].message
        except (IndexError, AttributeError):
            return None
        usage_metadata = getattr(message, "usage_metadata", None)
        if not usage_metadata:
            return None
        return {
            "prompt_tokens": int(usage_metadata.get("input_tokens") or 0),
            "completion_tokens": int(usage_metadata.get("output_tokens") or 0),
            "total_tokens": int(usage_metadata.get("total_tokens") or 0),
            "raw_usage": dict(usage_metadata),
        }
