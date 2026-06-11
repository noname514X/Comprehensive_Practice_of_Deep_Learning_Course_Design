from __future__ import annotations

import re
from pathlib import Path

from .config import KNOWLEDGE_DIR
from .models import KnowledgeChunk, SearchResult
from .vector_store import TfidfVectorStore


HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")


class KnowledgeBase:
    def __init__(self, knowledge_dir: Path = KNOWLEDGE_DIR, chunk_size: int = 620):
        self.knowledge_dir = knowledge_dir
        self.chunk_size = chunk_size
        self.chunks = self._load_chunks()
        self.store = TfidfVectorStore(self.chunks)

    def search(self, query: str, top_k: int = 3) -> list[SearchResult]:
        return self.store.search(query, top_k=top_k)

    def _load_chunks(self) -> list[KnowledgeChunk]:
        chunks: list[KnowledgeChunk] = []
        files = sorted(self.knowledge_dir.glob("*.md"))
        for path in files:
            chunks.extend(self._parse_file(path))
        return chunks

    def _parse_file(self, path: Path) -> list[KnowledgeChunk]:
        text = path.read_text(encoding="utf-8")
        section = "全文"
        buffer: list[str] = []
        chunks: list[KnowledgeChunk] = []
        section_index = 0

        def flush() -> None:
            nonlocal buffer, section_index
            content = "\n".join(line.strip() for line in buffer if line.strip()).strip()
            buffer = []
            if not content:
                return
            for part_index, part in enumerate(self._split_long_text(content)):
                chunks.append(
                    KnowledgeChunk(
                        chunk_id=f"{path.stem}-{section_index}-{part_index}",
                        source=path.name,
                        section=section,
                        text=part,
                    )
                )
            section_index += 1

        for line in text.splitlines():
            heading = HEADING_RE.match(line)
            if heading:
                flush()
                section = heading.group(2).strip()
                buffer.append(section)
                continue
            if not line.strip():
                flush()
                continue
            buffer.append(line)
        flush()
        return chunks

    def _split_long_text(self, text: str) -> list[str]:
        if len(text) <= self.chunk_size:
            return [text]
        pieces: list[str] = []
        start = 0
        overlap = min(90, self.chunk_size // 5)
        while start < len(text):
            end = min(len(text), start + self.chunk_size)
            pieces.append(text[start:end])
            if end == len(text):
                break
            start = max(0, end - overlap)
        return pieces
