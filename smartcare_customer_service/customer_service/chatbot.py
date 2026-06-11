from __future__ import annotations

from typing import Any

from .intent import IntentRecognizer
from .knowledge_base import KnowledgeBase
from .llm import LLMClient
from .memory import ConversationMemory
from .models import BotReply
from .tools import ServiceTools


class SmartCareBot:
    def __init__(
        self,
        knowledge_base: KnowledgeBase | None = None,
        memory: ConversationMemory | None = None,
        tools: ServiceTools | None = None,
        llm: LLMClient | None = None,
    ):
        self.knowledge_base = knowledge_base or KnowledgeBase()
        self.memory = memory or ConversationMemory()
        self.tools = tools or ServiceTools()
        self.llm = llm or LLMClient()
        self.recognizer = IntentRecognizer()

    def chat(self, message: str, session_id: str = "demo") -> BotReply:
        message = message.strip()
        if not message:
            return BotReply(session_id, "请输入需要咨询的问题。", "empty", "neutral", 1.0, None, [], [])

        state = self.memory.get_state(session_id)
        intent = self.recognizer.recognize(message, state)
        trace = [f"意图识别：{intent.intent}（置信度 {intent.confidence:.2f}）", f"情绪识别：{intent.emotion}"]
        self.memory.add_message(session_id, "user", message)

        updates: dict[str, str | None] = {}
        if intent.order_id:
            updates["last_order_id"] = intent.order_id
        if intent.product:
            updates["last_product"] = intent.product

        answer = ""
        tool_call: dict[str, Any] | None = None
        citations: list[dict[str, Any]] = []

        if intent.intent == "complaint" or intent.emotion == "angry":
            tool_call = {
                "name": "transfer_human",
                "arguments": {"reason": "强烈负面情绪或投诉", "priority": "high"},
                "result": self.tools.transfer_human("强烈负面情绪或投诉", priority="high"),
            }
            answer = (
                "非常抱歉给您带来不好的体验，我理解您现在很着急。"
                f"{tool_call['result']['message']}我也会把问题标记为高优先级。"
            )
            trace.append("触发高优先级转人工策略")

        elif intent.intent == "manual_transfer":
            tool_call = {
                "name": "transfer_human",
                "arguments": {"reason": "用户主动要求人工客服", "priority": "normal"},
                "result": self.tools.transfer_human("用户主动要求人工客服", priority="normal"),
            }
            answer = "好的，已为您转接人工客服。人工客服会接着当前对话继续处理。"
            trace.append("用户主动要求人工，调用 transfer_human")

        elif intent.intent == "order_status":
            order_id = intent.order_id or state.get("last_order_id")
            if not order_id:
                answer = "可以的，请提供订单号，我来帮您查询物流和预计送达时间。"
                updates["pending_intent"] = "order_status"
                trace.append("缺少订单号，进入订单查询待补充状态")
            else:
                result = self.tools.query_order(order_id)
                tool_call = {"name": "query_order", "arguments": {"order_id": order_id}, "result": result}
                answer = result["message"]
                if result.get("ok"):
                    updates["last_product"] = result.get("product")
                trace.append("调用工具 query_order")

        elif intent.intent == "return_exchange":
            order_id = intent.order_id or state.get("last_order_id")
            action = intent.action or state.get("preferred_action") or "售后处理"
            issue = self._summarize_issue(message)
            if "确认" in message or "对的" in message:
                issue = state.get("last_issue", issue)
            if not order_id:
                answer = "可以帮您处理售后。请先提供订单号，并说明希望退货退款、换货还是维修。"
                updates["pending_intent"] = "return_exchange"
                updates["last_issue"] = issue
                if intent.action:
                    updates["preferred_action"] = intent.action
                trace.append("缺少订单号，进入售后待补充状态")
            elif action == "售后处理" and not intent.action:
                answer = "已定位到订单。请问您希望退货退款、换货，还是维修？"
                updates["pending_intent"] = "return_exchange"
                updates["last_order_id"] = order_id
                updates["last_issue"] = issue
                trace.append("缺少处理方式，等待用户选择")
            else:
                ticket = self.tools.create_ticket(session_id, order_id, issue, action)
                self.memory.save_ticket(ticket)
                tool_call = {
                    "name": "create_ticket",
                    "arguments": {"order_id": order_id, "issue": issue, "action": action},
                    "result": ticket,
                }
                answer = (
                    f"好的，已根据订单 {order_id} 为您创建{action}工单。"
                    f"{ticket['message']}请保持手机畅通。"
                )
                updates["pending_intent"] = None
                updates["preferred_action"] = None
                trace.append("调用工具 create_ticket")

        elif intent.intent in {"product_info", "warranty"}:
            if "对比" in message or "区别" in message:
                result = self.tools.compare_products()
                tool_call = {"name": "compare_products", "arguments": {"left": "XX 蓝牙耳机", "right": "YY 游泳耳机"}, "result": result}
                if result["ok"]:
                    rows = "\n".join(
                        f"- {row['item']}：XX 为 {row['XX 蓝牙耳机']}；YY 为 {row['YY 游泳耳机']}"
                        for row in result["rows"]
                    )
                    answer = "两款耳机的核心区别如下：\n" + rows
                else:
                    answer = result["message"]
                trace.append("调用工具 compare_products")
            else:
                results = self.knowledge_base.search(message, top_k=3)
                citations = [item.to_dict() for item in results if item.score >= 0.05]
                if not citations:
                    answer = "知识库里没有找到足够相关的信息。我可以继续帮您转人工，或请您换个问法。"
                    trace.append("RAG 检索低于阈值")
                else:
                    answer = self.llm.answer_with_context(message, results)
                    trace.append(f"RAG 检索命中 {len(citations)} 个知识块")

        elif intent.intent == "smalltalk":
            answer = "您好，我是 SmartCare 智能客服。可以帮您查订单、处理退换货、解答产品参数和保修政策。"
            trace.append("闲聊引导回业务场景")

        else:
            results = self.knowledge_base.search(message, top_k=3)
            citations = [item.to_dict() for item in results if item.score >= 0.09]
            if citations:
                answer = self.llm.answer_with_context(message, results)
                trace.append("兜底路径中使用 RAG 回答")
            else:
                result = self.tools.transfer_human("知识库无法覆盖的问题", priority="normal")
                tool_call = {"name": "transfer_human", "arguments": {"reason": "知识库无法覆盖的问题"}, "result": result}
                answer = "这个问题我暂时无法根据现有知识库准确回答，已为您保留转人工入口。"
                trace.append("兜底转人工")

        self.memory.update_state(session_id, updates)
        reply = BotReply(
            session_id=session_id,
            answer=answer,
            intent=intent.intent,
            emotion=intent.emotion,
            confidence=intent.confidence,
            tool_call=tool_call,
            citations=citations,
            trace=trace,
        )
        self.memory.add_message(
            session_id,
            "assistant",
            answer,
            intent=intent.intent,
            emotion=intent.emotion,
            tool_call=tool_call,
            citations=citations,
        )
        return reply

    @staticmethod
    def _summarize_issue(message: str) -> str:
        cleaned = message.strip()
        if len(cleaned) <= 40:
            return cleaned
        return cleaned[:40] + "..."
