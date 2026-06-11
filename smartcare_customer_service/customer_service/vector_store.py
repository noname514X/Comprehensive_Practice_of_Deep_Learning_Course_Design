from __future__ import annotations

import math
import re
from collections import Counter
from typing import Iterable

from .models import KnowledgeChunk, SearchResult


TOKEN_RE = re.compile(r"[A-Za-z0-9]+|[\u4e00-\u9fff]+")
CHINESE_RE = re.compile(r"^[\u4e00-\u9fff]+$")
STOPWORDS = {
    "的",
    "了",
    "和",
    "是",
    "在",
    "吗",
    "呢",
    "我",
    "你",
    "们",
    "有",
    "为",
    "及",
    "与",
    "或",
}


def tokenize(text: str) -> list[str]:
    tokens: list[str] = []
    for part in TOKEN_RE.findall(text.lower()):
        if CHINESE_RE.match(part):
            tokens.extend(ch for ch in part if ch not in STOPWORDS)
            tokens.extend(part[i : i + 2] for i in range(max(0, len(part) - 1)))
            tokens.extend(part[i : i + 3] for i in range(max(0, len(part) - 2)))
        else:
            tokens.append(part)
    return [token for token in tokens if token and token not in STOPWORDS]


class TfidfVectorStore:
    """Small TF-IDF retriever for demos without external dependencies."""

    def __init__(self, chunks: Iterable[KnowledgeChunk] = ()):
        self.chunks: list[KnowledgeChunk] = []
        self.idf: dict[str, float] = {}
        self.vectors: list[dict[str, float]] = []
        if chunks:
            self.build(list(chunks))

    def build(self, chunks: list[KnowledgeChunk]) -> None:
        self.chunks = chunks
        document_frequency: Counter[str] = Counter()
        tokenized_docs: list[list[str]] = []
        for chunk in chunks:
            tokens = tokenize(chunk.text)
            tokenized_docs.append(tokens)
            document_frequency.update(set(tokens))

        total_docs = max(1, len(chunks))
        self.idf = {
            token: math.log((1 + total_docs) / (1 + freq)) + 1.0
            for token, freq in document_frequency.items()
        }
        self.vectors = [self._normalize(Counter(tokens)) for tokens in tokenized_docs]

    def search(self, query: str, top_k: int = 3) -> list[SearchResult]:
        if not self.chunks:
            return []
        query_vector = self._normalize(Counter(tokenize(query)))
        scored: list[SearchResult] = []
        for chunk, vector in zip(self.chunks, self.vectors):
            score = self._cosine(query_vector, vector)
            if score > 0:
                scored.append(SearchResult(chunk=chunk, score=score))
        scored.sort(key=lambda item: item.score, reverse=True)
        return scored[:top_k]

    def _normalize(self, counts: Counter[str]) -> dict[str, float]:
        weighted = {
            token: count * self.idf.get(token, 1.0)
            for token, count in counts.items()
        }
        norm = math.sqrt(sum(value * value for value in weighted.values()))
        if norm == 0:
            return {}
        return {token: value / norm for token, value in weighted.items()}

    @staticmethod
    def _cosine(left: dict[str, float], right: dict[str, float]) -> float:
        if not left or not right:
            return 0.0
        if len(left) > len(right):
            left, right = right, left
        return sum(value * right.get(token, 0.0) for token, value in left.items())
