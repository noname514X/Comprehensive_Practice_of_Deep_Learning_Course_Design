from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from .config import DEFAULT_DB_PATH, RUNTIME_DIR


class ConversationMemory:
    def __init__(self, db_path: Path = DEFAULT_DB_PATH):
        RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path
        self._init_db()

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        intent: str = "",
        emotion: str = "",
        tool_call: dict[str, Any] | None = None,
        citations: list[dict[str, Any]] | None = None,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO messages(session_id, role, content, intent, emotion, tool_call, citations)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    role,
                    content,
                    intent,
                    emotion,
                    json.dumps(tool_call or {}, ensure_ascii=False),
                    json.dumps(citations or [], ensure_ascii=False),
                ),
            )

    def recent_messages(self, session_id: str, limit: int = 30) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT role, content, intent, emotion, tool_call, citations, created_at
                FROM messages
                WHERE session_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (session_id, limit),
            ).fetchall()
        result = []
        for row in reversed(rows):
            result.append(
                {
                    "role": row["role"],
                    "content": row["content"],
                    "intent": row["intent"],
                    "emotion": row["emotion"],
                    "tool_call": json.loads(row["tool_call"] or "{}"),
                    "citations": json.loads(row["citations"] or "[]"),
                    "created_at": row["created_at"],
                }
            )
        return result

    def get_state(self, session_id: str) -> dict[str, str]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT key, value FROM session_state WHERE session_id = ?",
                (session_id,),
            ).fetchall()
        return {row["key"]: row["value"] for row in rows}

    def update_state(self, session_id: str, updates: dict[str, str | None]) -> None:
        with self._connect() as conn:
            for key, value in updates.items():
                if value is None:
                    conn.execute(
                        "DELETE FROM session_state WHERE session_id = ? AND key = ?",
                        (session_id, key),
                    )
                else:
                    conn.execute(
                        """
                        INSERT INTO session_state(session_id, key, value)
                        VALUES (?, ?, ?)
                        ON CONFLICT(session_id, key) DO UPDATE SET value = excluded.value
                        """,
                        (session_id, key, value),
                    )

    def save_ticket(self, ticket: dict[str, Any]) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO tickets(ticket_id, session_id, order_id, issue, action, priority, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    ticket["ticket_id"],
                    ticket.get("session_id", ""),
                    ticket.get("order_id", ""),
                    ticket.get("issue", ""),
                    ticket.get("action", ""),
                    ticket.get("priority", ""),
                    ticket.get("status", ""),
                ),
            )

    def metrics(self) -> dict[str, Any]:
        with self._connect() as conn:
            total_messages = conn.execute("SELECT COUNT(*) AS n FROM messages").fetchone()["n"]
            total_sessions = conn.execute("SELECT COUNT(DISTINCT session_id) AS n FROM messages").fetchone()["n"]
            total_tickets = conn.execute("SELECT COUNT(*) AS n FROM tickets").fetchone()["n"]
            intent_rows = conn.execute(
                """
                SELECT intent, COUNT(*) AS n FROM messages
                WHERE role = 'assistant' AND intent != ''
                GROUP BY intent
                ORDER BY n DESC
                """
            ).fetchall()
        return {
            "messages": total_messages,
            "sessions": total_sessions,
            "tickets": total_tickets,
            "intent_distribution": {row["intent"]: row["n"] for row in intent_rows},
        }

    def reset(self, session_id: str | None = None) -> None:
        with self._connect() as conn:
            if session_id:
                conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
                conn.execute("DELETE FROM session_state WHERE session_id = ?", (session_id,))
            else:
                conn.execute("DELETE FROM messages")
                conn.execute("DELETE FROM session_state")
                conn.execute("DELETE FROM tickets")

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    intent TEXT DEFAULT '',
                    emotion TEXT DEFAULT '',
                    tool_call TEXT DEFAULT '{}',
                    citations TEXT DEFAULT '[]',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS session_state (
                    session_id TEXT NOT NULL,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    PRIMARY KEY(session_id, key)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tickets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticket_id TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    order_id TEXT,
                    issue TEXT,
                    action TEXT,
                    priority TEXT,
                    status TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
