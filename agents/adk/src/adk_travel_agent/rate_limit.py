from __future__ import annotations

import asyncio
import json
import math
import time
from collections import deque
from typing import Any

INVOCATION_METHODS = {"message/send", "message/stream"}
REST_INVOCATION_PATHS = {"/rest/message:send", "/rest/message:stream"}


class InvocationRateLimitMiddleware:
    """Small process-local global limiter for new A2A executions."""

    def __init__(self, app: Any, *, enabled: bool, requests: int, window_seconds: int):
        self.app = app
        self.enabled = enabled
        self.requests = requests
        self.window_seconds = window_seconds
        self.timestamps: deque[float] = deque()
        self.lock = asyncio.Lock()

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        if not self.enabled or scope.get("type") != "http" or scope.get("method") != "POST":
            await self.app(scope, receive, send)
            return

        body = b""
        replay_receive = receive
        path = scope.get("path", "")
        is_invocation = path in REST_INVOCATION_PATHS
        if path == "/":
            chunks: list[bytes] = []
            while True:
                message = await receive()
                chunks.append(message.get("body", b""))
                if not message.get("more_body", False):
                    break
            body = b"".join(chunks)
            try:
                is_invocation = json.loads(body).get("method") in INVOCATION_METHODS
            except (json.JSONDecodeError, AttributeError):
                is_invocation = False

            delivered = False

            async def replay() -> dict[str, Any]:
                nonlocal delivered
                if delivered:
                    return {"type": "http.disconnect"}
                delivered = True
                return {"type": "http.request", "body": body, "more_body": False}

            replay_receive = replay

        if not is_invocation:
            await self.app(scope, replay_receive, send)
            return

        now = time.monotonic()
        async with self.lock:
            while self.timestamps and now - self.timestamps[0] >= self.window_seconds:
                self.timestamps.popleft()
            if len(self.timestamps) < self.requests:
                self.timestamps.append(now)
                retry_after = 0
            else:
                retry_after = max(1, math.ceil(self.window_seconds - (now - self.timestamps[0])))

        if retry_after == 0:
            await self.app(scope, replay_receive, send)
            return

        payload = json.dumps(
            {"error": "rate_limit_exceeded", "retry_after_seconds": retry_after}
        ).encode()
        await send(
            {
                "type": "http.response.start",
                "status": 429,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"content-length", str(len(payload)).encode()),
                    (b"retry-after", str(retry_after).encode()),
                ],
            }
        )
        await send({"type": "http.response.body", "body": payload})
