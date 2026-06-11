from __future__ import annotations

import argparse
import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .chatbot import SmartCareBot
from .config import STATIC_DIR


class SmartCareHandler(BaseHTTPRequestHandler):
    bot = SmartCareBot()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self._serve_file(STATIC_DIR / "index.html")
            return
        if parsed.path.startswith("/static/"):
            self._serve_file(STATIC_DIR / parsed.path.removeprefix("/static/"))
            return
        if parsed.path == "/api/history":
            query = parse_qs(parsed.query)
            session_id = query.get("session_id", ["demo"])[0]
            self._json({"messages": self.bot.memory.recent_messages(session_id)})
            return
        if parsed.path == "/api/metrics":
            self._json(self.bot.memory.metrics())
            return
        if parsed.path == "/api/health":
            self._json({"ok": True, "chunks": len(self.bot.knowledge_base.chunks)})
            return
        self.send_error(404)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        payload = self._read_json()
        if parsed.path == "/api/chat":
            message = str(payload.get("message", ""))
            session_id = str(payload.get("session_id", "demo"))
            reply = self.bot.chat(message, session_id=session_id)
            self._json(reply.to_dict())
            return
        if parsed.path == "/api/reset":
            session_id = payload.get("session_id")
            self.bot.memory.reset(str(session_id) if session_id else None)
            self._json({"ok": True})
            return
        self.send_error(404)

    def log_message(self, format: str, *args: object) -> None:
        print(f"[SmartCare] {self.address_string()} {format % args}")

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if not length:
            return {}
        raw = self.rfile.read(length).decode("utf-8")
        return json.loads(raw or "{}")

    def _json(self, data: dict, status: int = 200) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve_file(self, path: Path) -> None:
        if not path.exists() or not path.is_file():
            self.send_error(404)
            return
        body = path.read_bytes()
        content_type, _ = mimetypes.guess_type(path.name)
        self.send_response(200)
        self.send_header("Content-Type", content_type or "application/octet-stream")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def run(host: str = "127.0.0.1", port: int = 8000) -> None:
    server = ThreadingHTTPServer((host, port), SmartCareHandler)
    print(f"SmartCare is running at http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nSmartCare stopped.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run SmartCare customer service web app.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8000, type=int)
    args = parser.parse_args()
    run(args.host, args.port)


if __name__ == "__main__":
    main()
