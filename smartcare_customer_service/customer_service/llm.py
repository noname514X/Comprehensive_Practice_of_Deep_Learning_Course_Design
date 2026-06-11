from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request

from .models import SearchResult


class LLMClient:
    """Ollama wrapper with a deterministic fallback for offline demos."""

    def __init__(self, model: str | None = None, use_ollama: bool | None = None):
        self.model = model or os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b")
        if use_ollama is None:
            use_ollama = os.getenv("USE_OLLAMA", "").lower() in {"1", "true", "yes"}
        self.use_ollama = use_ollama

    def answer_with_context(self, question: str, results: list[SearchResult]) -> str:
        if not results:
            return "根据当前知识库，我没有找到足够相关的资料。建议换一种问法，或转人工客服继续处理。"

        context = "\n\n".join(
            f"[{index + 1}] 来源：{item.chunk.source} / {item.chunk.section}\n{item.chunk.text}"
            for index, item in enumerate(results)
        )
        prompt = (
            "你是电商耳机售后客服。请只依据给定资料回答用户问题，回答要简洁、礼貌，"
            "如果资料不足要说明无法确认。回答末尾不要编造不存在的来源。\n\n"
            f"资料：\n{context}\n\n用户问题：{question}\n\n客服回答："
        )
        if self.use_ollama:
            generated = self._ollama_generate(prompt)
            if generated:
                return generated
        return self._fallback_answer(question, results)

    def _ollama_generate(self, prompt: str) -> str | None:
        payload = json.dumps(
            {"model": self.model, "prompt": prompt, "stream": False},
            ensure_ascii=False,
        ).encode("utf-8")
        request = urllib.request.Request(
            "http://127.0.0.1:11434/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                data = json.loads(response.read().decode("utf-8"))
                return data.get("response", "").strip() or None
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
            return None

    @staticmethod
    def _fallback_answer(question: str, results: list[SearchResult]) -> str:
        top = results[0].chunk.text
        sentences = [item.strip() for item in re.split(r"[。！？\n]", top) if item.strip()]
        selected = sentences[:3] if sentences else [top[:180]]
        answer = "。".join(selected)
        if answer and not answer.endswith("。"):
            answer += "。"
        if "游泳" in question and "不建议" in top:
            answer += "因此如果要游泳佩戴，建议选择防水等级更高的 YY 游泳耳机。"
        return answer
