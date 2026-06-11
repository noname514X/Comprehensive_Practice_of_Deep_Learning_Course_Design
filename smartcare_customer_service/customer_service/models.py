from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class KnowledgeChunk:
    chunk_id: str
    source: str
    section: str
    text: str


@dataclass
class SearchResult:
    chunk: KnowledgeChunk
    score: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "chunk_id": self.chunk.chunk_id,
            "source": self.chunk.source,
            "section": self.chunk.section,
            "text": self.chunk.text,
            "score": round(self.score, 4),
        }


@dataclass
class IntentResult:
    intent: str
    emotion: str
    confidence: float
    order_id: str | None = None
    product: str | None = None
    action: str | None = None
    reason: str = ""


@dataclass
class BotReply:
    session_id: str
    answer: str
    intent: str
    emotion: str
    confidence: float
    tool_call: dict[str, Any] | None
    citations: list[dict[str, Any]]
    trace: list[str]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["tool_call"] = self.tool_call or None
        return data
