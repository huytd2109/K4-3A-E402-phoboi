from __future__ import annotations

import json
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from phoboi.analyzer import MessageAnalyzer
from phoboi.config import Settings
from phoboi.policy import decide
from phoboi.providers.factory import create_provider
from phoboi.security import sanitize_exception
from phoboi.sources import source_store_for_mode


class ApiHandler(BaseHTTPRequestHandler):
    server_version = "PhoboiAPI/1.0"

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "http://localhost:8443")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:  # noqa: N802
        self._send_json(204, {})

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/api/chat":
            self._send_json(404, {"error": "Not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length))
            message = payload.get("message") if isinstance(payload, dict) else None
            if not isinstance(message, str) or not message.strip():
                self._send_json(400, {"error": "message must be a non-empty string"})
                return
            if len(message) > 4000:
                self._send_json(400, {"error": "message is too long"})
                return

            settings = Settings.from_env()
            store = source_store_for_mode(settings.source_mode, app_env=settings.app_env)
            analysis_response = MessageAnalyzer(
                create_provider(settings), model=settings.llm_model
            ).analyze_batch([(f"UI-{uuid.uuid4().hex[:12]}", message, None)])
            analysis = analysis_response.data.results[0]
            decision = decide(analysis, message, store)
            self._send_json(
                200,
                {
                    "decision": decision.model_dump(mode="json"),
                    "provider": analysis_response.provider,
                    "model": analysis_response.model,
                    "live": analysis_response.live,
                    "latency_ms": analysis_response.latency_ms,
                },
            )
        except Exception as exc:  # Keep provider details and secrets out of responses.
            self._send_json(502, {"error": sanitize_exception(exc)})

    def log_message(self, format: str, *args: Any) -> None:
        print(f"[phoboi-api] {format % args}")


def main() -> None:
    host = "127.0.0.1"
    port = 8787
    server = ThreadingHTTPServer((host, port), ApiHandler)
    print(f"Phoboi API listening at http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
