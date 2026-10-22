"""The desk's operations in one module: its logs as JSON lines with each request's id, its
readiness at /ready, and the server's settings from the environment.

    uv run desk_ops.py
"""

import asyncio
import json
import logging
import os
import re
import secrets
import sys
import time
from collections.abc import Awaitable, Callable, Mapping, MutableMapping
from contextvars import ContextVar
from datetime import UTC, datetime
from http import HTTPStatus
from typing import Any

import httpx
import serve
import uvicorn
from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import JSONResponse
from psycopg_pool import ConnectionPool
from starlette.concurrency import run_in_threadpool

Scope = MutableMapping[str, Any]
Message = MutableMapping[str, Any]
Receive = Callable[[], Awaitable[Message]]
Send = Callable[[Message], Awaitable[None]]
App = Callable[[Scope, Receive, Send], Awaitable[None]]
Check = Callable[[], Awaitable[None]]

request_id: ContextVar[str | None] = ContextVar("request_id", default=None)

STANDARD = set(vars(logging.makeLogRecord({}))) | {"message", "asctime", "taskName"}
SECRET = re.compile(
    r"authorization|cookie|database_url|password|secret|token", re.IGNORECASE
)
HIDDEN = "[hidden]"
GIVEN_ID = re.compile(r"[A-Za-z0-9._-]{1,64}")
CHECK_SECONDS = 2.0
SHUTDOWN_SECONDS = 25
LOOPBACK = "127.0.0.1,::1"


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
    """A record as one line of JSON, with the request it came from."""

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
    """Gives each request an id, sends it back in X-Request-ID, and logs the request."""

    def __init__(self, app: App, logger: logging.Logger | None = None) -> None:
        self.app = app
        self.logger = logger or logging.getLogger("desk.requests")

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        given = dict(scope["headers"]).get(b"x-request-id", b"").decode("latin-1")
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
            # The whole address, so a line shows exactly what the caller asked for.
            target = scope["path"]
            if scope["query_string"]:
                target += "?" + scope["query_string"].decode("latin-1")
            self.logger.info(
                "request",
                extra={
                    "method": scope["method"],
                    "path": target,
                    "status": status,
                    "ms": round((time.perf_counter() - started) * 1000, 1),
                },
            )
            request_id.reset(token)


def database_check(pool: ConnectionPool) -> Check:
    """A check that the database answers a query."""

    def query() -> None:
        with pool.connection(timeout=CHECK_SECONDS) as conn:
            conn.execute("SELECT 1")

    async def check() -> None:
        await run_in_threadpool(query)

    return check


def model_check(client: httpx.AsyncClient) -> Check:
    """A check that the model answers."""

    async def check() -> None:
        # A token from the model shows it answers, not only that its server is up.
        response = await client.post(
            "/chat/completions",
            json={"messages": [{"role": "user", "content": "Hi"}], "max_tokens": 1},
        )
        response.raise_for_status()

    return check


async def readiness(checks: Mapping[str, Check]) -> dict[str, str]:
    """Each check's state, "ok" or what went wrong, with every check run at once."""

    async def state(check: Check) -> str:
        # Each check has a timeout of its own: the pool's, and the client's.
        try:
            await check()
        except Exception as error:  # Whatever went wrong, the desk isn't ready.
            return str(error) or type(error).__name__
        return "ok"

    states = await asyncio.gather(*(state(check) for check in checks.values()))
    return dict(zip(checks, states, strict=True))


router = APIRouter()


@router.get("/ready")
async def ready(request: Request) -> JSONResponse:
    """200 with each check's state when every one is ok, and otherwise 503."""
    states = await readiness(
        {
            "database": database_check(request.app.state.pool),
            "model": model_check(request.app.state.client),
        }
    )
    failing = [name for name, state in states.items() if state != "ok"]
    if not failing:
        return JSONResponse({"checks": states})
    status = HTTPStatus.SERVICE_UNAVAILABLE
    return JSONResponse(
        {
            "type": "about:blank",
            "title": status.phrase,
            "status": status,
            "detail": f"Not ready: {', '.join(failing)}.",
            "checks": states,
        },
        status_code=status,
        media_type="application/problem+json",
    )


def production(app: FastAPI) -> FastAPI:
    """The app with its readiness at /ready and an id for each request in its logs."""
    app.include_router(router)
    app.add_middleware(RequestIds)
    return app


def create() -> FastAPI:
    """The desk with its page, its logs sent to standard output as JSON."""
    configure()
    return production(serve.create())


def port_from(environ: Mapping[str, str]) -> int:
    """The port in PORT, or 8000 if it isn't set."""
    text = environ.get("PORT", "8000")
    if not text.isdigit() or not 1 <= int(text) <= 65535:
        raise ValueError("PORT should be a port from 1 to 65535.")
    return int(text)


def config(environ: Mapping[str, str]) -> uvicorn.Config:
    """The server's settings, from the environment."""
    return uvicorn.Config(
        "desk_ops:create",
        factory=True,
        # Only this machine reaches the desk: the host's proxy sends it the callers.
        host="127.0.0.1",
        port=port_from(environ),
        proxy_headers=True,
        forwarded_allow_ips=environ.get("FORWARDED_ALLOW_IPS", LOOPBACK),
        timeout_graceful_shutdown=SHUTDOWN_SECONDS,
        log_config=None,
        access_log=False,
    )


if __name__ == "__main__":
    uvicorn.Server(config(os.environ)).run()
