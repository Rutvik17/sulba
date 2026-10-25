"""The desk's logs: one JSON object a line, each with the request it came from, and none of
the secrets a request or a setting holds."""

import logging
from collections.abc import Awaitable, Callable, MutableMapping
from contextvars import ContextVar
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


def redacted(value: Any) -> Any:
    """The value, with the value of every key that names a secret hidden, at any depth."""
    raise NotImplementedError


class JsonFormatter(logging.Formatter):
    """A record as one line of JSON: its time in UTC, level, logger and message, the request
    it came from, its extra fields, and its error's traceback."""

    def format(self, record: logging.LogRecord) -> str:
        raise NotImplementedError


def configure(level: int = logging.INFO) -> None:
    """Sends every log record to standard output, as JSON."""
    raise NotImplementedError


class RequestIds:
    """ASGI middleware that gives each request an id, the caller's own if it's a fit one,
    sends it back in X-Request-ID, and logs one line for the request once it's answered."""

    def __init__(self, app: App, logger: logging.Logger | None = None) -> None:
        self.app = app
        self.logger = logger or logging.getLogger("desk.requests")

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        raise NotImplementedError
