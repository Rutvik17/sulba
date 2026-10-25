"""Whether the desk is ready for callers: its database answers, and its model is loaded.
A platform asks before it sends the desk callers, and stops sending them while it isn't."""

from collections.abc import Awaitable, Callable, Mapping

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from psycopg_pool import ConnectionPool

# How long each check has: a platform asks every few seconds, and waits for an answer.
CHECK_SECONDS = 2.0

Check = Callable[[], Awaitable[None]]

router = APIRouter()


def database_check(pool: ConnectionPool) -> Check:
    """A check that the database answers a query, on a connection from the pool."""
    raise NotImplementedError


def model_check(client: httpx.AsyncClient) -> Check:
    """A check that the model's server has loaded the model: its /health answers 200, and
    503 while it loads."""
    raise NotImplementedError


async def readiness(
    checks: Mapping[str, Check], seconds: float = CHECK_SECONDS
) -> dict[str, str]:
    """Each check's state, "ok" or what went wrong, with every check run at once and each
    given `seconds`."""
    raise NotImplementedError


@router.get("/ready")
async def ready(request: Request) -> JSONResponse:
    """200 with each check's state when every one is ok, and otherwise 503 with them, as
    problem details."""
    raise NotImplementedError
