"""Whether the desk is ready for callers: its database answers, and its model is loaded.
A platform asks before it sends the desk callers, and stops sending them while it isn't."""

import asyncio
from collections.abc import Awaitable, Callable, Mapping
from http import HTTPStatus

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from psycopg_pool import ConnectionPool
from starlette.concurrency import run_in_threadpool

# How long each check has: a platform asks every few seconds, and waits for an answer.
CHECK_SECONDS = 2.0

Check = Callable[[], Awaitable[None]]

router = APIRouter()


def database_check(pool: ConnectionPool) -> Check:
    """A check that the database answers a query, on a connection from the pool."""

    def query() -> None:
        with pool.connection(timeout=CHECK_SECONDS) as conn:
            conn.execute("SELECT 1")

    async def check() -> None:
        await run_in_threadpool(query)

    return check


def model_check(client: httpx.AsyncClient) -> Check:
    """A check that the model's server has loaded the model: its /health answers 200, and
    503 while it loads."""

    async def check() -> None:
        response = await client.get("/health")
        if response.status_code == HTTPStatus.SERVICE_UNAVAILABLE:
            raise RuntimeError("The model is still loading.")
        response.raise_for_status()

    return check


async def readiness(
    checks: Mapping[str, Check], seconds: float = CHECK_SECONDS
) -> dict[str, str]:
    """Each check's state, "ok" or what went wrong, with every check run at once and each
    given `seconds`."""

    async def state(check: Check) -> str:
        try:
            await asyncio.wait_for(check(), seconds)
        except TimeoutError:
            return f"No answer in {seconds:g} seconds."
        except Exception as error:  # Whatever went wrong, the desk isn't ready.
            return str(error) or type(error).__name__
        return "ok"

    states = await asyncio.gather(*(state(check) for check in checks.values()))
    return dict(zip(checks, states, strict=True))


def checks_of(request: Request) -> dict[str, Check]:
    """The desk's checks, on the pool and the model's client its lifespan made."""
    return {
        "database": database_check(request.app.state.pool),
        "model": model_check(request.app.state.client),
    }


@router.get("/ready")
async def ready(request: Request) -> JSONResponse:
    """200 with each check's state when every one is ok, and otherwise 503 with them, as
    problem details."""
    states = await readiness(checks_of(request))
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
