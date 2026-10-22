"""The desk's logs: one JSON object a line, each with the request it came from, and none of
the secrets a request or a setting holds."""

import json
import logging
import re
import secrets
import sys
import time
from collections.abc import Awaitable, Callable, MutableMapping
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any

Scope = MutableMapping[str, Any]
Message = MutableMapping[str, Any]
Receive = Callable[[], Awaitable[Message]]
Send = Callable[[Message], Awaitable[None]]
App = Callable[[Scope, Receive, Send], Awaitable[None]]

# The id of the request the code is answering, if it's answering one.
request_id: ContextVar[str | None] = ContextVar("request_id", default=None)

# What every log record has, so what else it has came from the call's extra.
STANDARD = set(vars(logging.makeLogRecord({}))) | {"message", "asctime", "taskName"}
SECRET = re.compile(
    r"authorization|cookie|database_url|password|secret|token", re.IGNORECASE
)
HIDDEN = "[hidden]"
GIVEN_ID = re.compile(r"[A-Za-z0-9._-]{1,64}")


def redacted(value: Any) -> Any:
    """The value, with the value of every key that names a secret hidden, at any depth."""
    if isinstance(value, dict):
        return {
            key: HIDDEN if SECRET.search(str(key)) else redacted(inner)
            for key, inner in value.items()
        }
    if isinstance(value, list | tuple):
        return [redacted(inner) for inner in value]
    return value


class JsonFormatter(logging.Formatter):
    """A record as one line of JSON: its time in UTC, level, logger and message, the request
    it came from, its extra fields, and its error's traceback."""

    def format(self, record: logging.LogRecord) -> str:
        entry: dict[str, Any] = {
            "time": datetime.fromtimestamp(record.created, UTC).isoformat(
                timespec="milliseconds"
            ),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        current = request_id.get()
        if current is not None:
            entry["request_id"] = current
        entry.update(
            (key, value) for key, value in vars(record).items() if key not in STANDARD
        )
        if record.exc_info:
            entry["error"] = self.formatException(record.exc_info)
        return json.dumps(redacted(entry), default=str)


def configure(level: int = logging.INFO) -> None:
    """Sends every log record to standard output, as JSON."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(level)


class RequestIds:
    """ASGI middleware that gives each request an id, the caller's own if it's a fit one,
    sends it back in X-Request-ID, and logs one line for the request once it's answered."""

    def __init__(self, app: App, logger: logging.Logger | None = None) -> None:
        self.app = app
        self.logger = logger or logging.getLogger("desk.requests")

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        given = dict(scope["headers"]).get(b"x-request-id", b"").decode("latin-1")
        # An id from outside goes into every line, so only a short, plain one is kept.
        current = given if GIVEN_ID.fullmatch(given) else secrets.token_hex(8)
        token = request_id.set(current)
        status = 500
        started = time.perf_counter()

        async def sending(message: Message) -> None:
            nonlocal status
            if message["type"] == "http.response.start":
                status = message["status"]
                message["headers"] = [
                    *message.get("headers", []),
                    (b"x-request-id", current.encode()),
                ]
            await send(message)

        try:
            await self.app(scope, receive, sending)
        finally:
            # The path without its query, which can hold a token or a person's details.
            self.logger.info(
                "request",
                extra={
                    "method": scope["method"],
                    "path": scope["path"],
                    "status": status,
                    "ms": round((time.perf_counter() - started) * 1000, 1),
                },
            )
            request_id.reset(token)
