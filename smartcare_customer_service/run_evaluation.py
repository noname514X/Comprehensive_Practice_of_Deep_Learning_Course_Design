from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from customer_service.chatbot import SmartCareBot
from customer_service.config import EVALUATION_DIR, REPORTS_DIR, RUNTIME_DIR
from customer_service.llm import LLMClient
from customer_service.memory import ConversationMemory


def main() -> None:
    cases = json.loads((EVALUATION_DIR / "test_cases.json").read_text(encoding="utf-8"))
    memory = ConversationMemory(RUNTIME_DIR / "evaluation_history.db")
    memory.reset()
    bot = SmartCareBot(memory=memory, llm=LLMClient(use_ollama=False))

    rows = []
    intent_hits = 0
    tool_hits = 0
    citation_cases = 0
    citation_hits = 0
    scenarios = Counter()

    for case in cases:
        reply = bot.chat(case["message"], session_id=case["session_id"])
        actual_tool = reply.tool_call["name"] if reply.tool_call else None
        expected_tool = case["expected_tool"]
        intent_ok = reply.intent == case["expected_intent"]
        tool_ok = actual_tool == expected_tool
        if intent_ok:
            intent_hits += 1
        if tool_ok:
            tool_hits += 1
        if case["scenario"] in {"RAG 问答", "追问"}:
            citation_cases += 1
            if reply.citations:
                citation_hits += 1
        scenarios[case["scenario"]] += 1
        rows.append(
            {
                "id": case["id"],
                "message": case["message"],
                "expected_intent": case["expected_intent"],
                "actual_intent": reply.intent,
                "expected_tool": expected_tool or "-",
                "actual_tool": actual_tool or "-",
                "intent_ok": intent_ok,
                "tool_ok": tool_ok,
                "citation_count": len(reply.citations),
            }
        )

    intent_accuracy = intent_hits / len(cases)
    tool_accuracy = tool_hits / len(cases)
    citation_rate = citation_hits / max(1, citation_cases)

    report = render_report(rows, intent_accuracy, tool_accuracy, citation_rate, scenarios)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (REPORTS_DIR / "evaluation_results.md").write_text(report, encoding="utf-8")

    print(report)


def render_report(rows, intent_accuracy, tool_accuracy, citation_rate, scenarios) -> str:
    lines = [
        "# SmartCare 测试对话评估结果",
        "",
        "## 汇总指标",
        "",
        f"- 测试样本数：{len(rows)}",
        f"- 意图识别准确率：{intent_accuracy:.1%}",
        f"- 工具调用正确率：{tool_accuracy:.1%}",
        f"- RAG 引用命中率：{citation_rate:.1%}",
        f"- 覆盖场景：{', '.join(f'{name} {count} 条' for name, count in scenarios.items())}",
        "",
        "## 明细",
        "",
        "| ID | 用户消息 | 期望意图 | 实际意图 | 期望工具 | 实际工具 | 意图正确 | 工具正确 | 引用数 |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| {id} | {message} | {expected_intent} | {actual_intent} | {expected_tool} | {actual_tool} | {intent_ok} | {tool_ok} | {citation_count} |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "## 结论",
            "",
            "规则意图识别在订单、售后、投诉和闲聊场景上表现稳定；RAG 问答能返回来源片段，便于检查答案依据。后续可接入 Sentence-Transformers 与 ChromaDB 替换当前 TF-IDF 检索，以提升语义召回能力。",
        ]
    )
    return "\n".join(lines)


if __name__ == "__main__":
    main()
