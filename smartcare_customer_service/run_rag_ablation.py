from __future__ import annotations

import json

from customer_service.config import EVALUATION_DIR, REPORTS_DIR
from customer_service.knowledge_base import KnowledgeBase


def main() -> None:
    questions = json.loads((EVALUATION_DIR / "rag_questions.json").read_text(encoding="utf-8"))
    kb = KnowledgeBase()
    top_ks = [1, 3, 5]
    rows = []

    for item in questions:
        expected = set(item["expected_sources"])
        row = {"question": item["question"]}
        for top_k in top_ks:
            results = kb.search(item["question"], top_k=top_k)
            sources = [result.chunk.source for result in results]
            row[f"top_{top_k}_sources"] = sources
            row[f"top_{top_k}_hit"] = any(source in expected for source in sources)
        rows.append(row)

    lines = [
        "# RAG 检索参数消融实验",
        "",
        "## 指标说明",
        "",
        "每个问题预先标注 1-2 个正确资料来源；检索返回的 Top-K 文档块中只要包含任一正确来源，就记为命中。",
        "",
        "## 结果",
        "",
        "| 问题 | Top-1 | Top-3 | Top-5 | Top-3 来源 |",
        "| --- | --- | --- | --- | --- |",
    ]
    summary = {top_k: 0 for top_k in top_ks}
    for row in rows:
        for top_k in top_ks:
            summary[top_k] += int(row[f"top_{top_k}_hit"])
        lines.append(
            "| {question} | {top1} | {top3} | {top5} | {sources} |".format(
                question=row["question"],
                top1="命中" if row["top_1_hit"] else "未命中",
                top3="命中" if row["top_3_hit"] else "未命中",
                top5="命中" if row["top_5_hit"] else "未命中",
                sources=", ".join(row["top_3_sources"]),
            )
        )
    lines.extend(
        [
            "",
            "## 命中率",
            "",
            *[f"- Top-{top_k}：{summary[top_k] / len(rows):.1%}" for top_k in top_ks],
            "",
            "## 分析",
            "",
            "Top-1 对问题表述更敏感，适合回答较明确的问题；Top-3 在召回和上下文长度之间更平衡，因此系统默认使用 top_k=3。Top-5 能提高召回，但会把相邻政策段落一起带入 Prompt，增加回答冗余和潜在干扰。",
        ]
    )
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report = "\n".join(lines)
    (REPORTS_DIR / "rag_ablation.md").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
