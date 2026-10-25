"""The desk's app on Postgres: its settings from the environment, the database migrated as the
app starts, conversations and turns kept there, and each day's usage for the dashboard.

    uv run uvicorn app:create_app --factory
"""

import os
from collections.abc import AsyncIterator, Mapping
from contextlib import asynccontextmanager
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import httpx
from fastapi import FastAPI, Query, Request
from psycopg_pool import ConnectionPool
from pydantic import BaseModel, Field, ValidationError

from agent import Agent
from conversations import install
from conversations import router as conversations_router
from desk import TICKETS, Actions, Desk, free_times, load_search
from gate import Gate
from migrations import migrate
from replies import Agents
from replies import router as replies_router
from store import Store

# Each setting's environment variable, and its value when the variable isn't set, if it has one.
VARIABLES = {
    "model_url": ("DESK_MODEL_URL", "http://127.0.0.1:9931/v1"),
    "database_url": ("DESK_DATABASE_URL", None),
    "running": ("DESK_RUNNING", "1"),
    "waiting": ("DESK_WAITING", "8"),
    "seconds": ("DESK_SECONDS", "120"),
}


class Settings(BaseModel):
    """Where the model answers and the database is, how many replies run and wait at once, and
    each one's limit."""

    model_url: str = Field(pattern=r"^https?://")
    database_url: str = Field(pattern=r"^postgres(ql)?://")
    running: int = Field(ge=1)
    waiting: int = Field(ge=0)
    seconds: float = Field(gt=0)


class Day(BaseModel):
    """A day's turns, in UTC: how many there were and how many were done, their tokens, and the
    median and 90th percentile of their seconds."""

    day: date
    turns: int
    done: int
    prompt_tokens: int
    completion_tokens: int
    p50_seconds: float
    p90_seconds: float


def settings_from(environ: Mapping[str, str]) -> Settings:
    """The settings from the environment's variables, each one's default where it isn't set. A
    value that doesn't fit, or a variable with no default that isn't set, raises ValueError,
    naming every variable that's wrong."""
    given = {
        name: environ.get(variable, default)
        for name, (variable, default) in VARIABLES.items()
    }
    try:
        return Settings(**given)
    except ValidationError as error:
        wrong = [VARIABLES[str(each["loc"][0])][0] for each in error.errors()]
        raise ValueError(f"These settings don't fit: {', '.join(wrong)}.") from error


def create_app(
    settings: Settings | None = None,
    data: Path = Path("data"),
    client: httpx.AsyncClient | None = None,
) -> FastAPI:
    """The app, with the settings given, or those of the environment, the help pages in data,
    and the client given to the model, or one it makes from the settings and closes as it
    stops."""
    chosen = settings or settings_from(os.environ)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        # A reply can take as long as its limit, so the client waits that long for each read.
        timeout = httpx.Timeout(chosen.seconds, connect=10)
        model = client or httpx.AsyncClient(base_url=chosen.model_url, timeout=timeout)
        # Every running reply and every request for a conversation can hold a connection.
        pool = ConnectionPool(
            chosen.database_url,
            min_size=1,
            max_size=chosen.running + 4,
            kwargs={"autocommit": True},
            open=False,
        )
        try:
            pool.open(wait=True, timeout=10)
            with pool.connection() as conn:
                migrate(conn)
            desk = Desk(load_search(model, data), TICKETS, free_times())
            app.state.client = model
            app.state.pool = pool
            app.state.desk = desk
            app.state.conversations = Store(pool)
            app.state.gate = Gate(chosen.running, chosen.waiting, chosen.seconds)
            app.state.agents = Agents(lambda page: Agent(model, Actions(desk), page))
            yield
        finally:
            pool.close()
            if client is None:
                await model.aclose()

    app = FastAPI(title="The help desk", lifespan=lifespan)
    install(app)
    app.include_router(conversations_router)
    app.include_router(replies_router)

    @app.get("/health")
    def health() -> dict[str, str]:
        """Whether the app is up, without asking the model or the database anything."""
        return {"status": "ok"}

    @app.get("/usage")
    def usage(request: Request, days: int = Query(7, ge=1, le=90)) -> list[Day]:
        """Each of the last days' usage, today's included, for the days with turns."""
        since = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        since -= timedelta(days=days - 1)
        pool: ConnectionPool = request.app.state.pool
        with pool.connection() as conn:
            # started_at itself is compared, so the index on it finds the days' turns.
            rows = conn.execute(
                """
                SELECT (started_at AT TIME ZONE 'UTC')::date AS day,
                    count(*),
                    count(*) FILTER (WHERE outcome = 'done'),
                    sum(prompt_tokens),
                    sum(completion_tokens),
                    percentile_cont(0.5) WITHIN GROUP (ORDER BY seconds),
                    percentile_cont(0.9) WITHIN GROUP (ORDER BY seconds)
                FROM turns
                WHERE started_at >= %s
                GROUP BY day
                ORDER BY day
                """,
                [since],
            ).fetchall()
        return [
            Day(
                day=day,
                turns=turns,
                done=done,
                prompt_tokens=prompt,
                completion_tokens=completion,
                p50_seconds=p50,
                p90_seconds=p90,
            )
            for day, turns, done, prompt, completion, p50, p90 in rows
        ]

    return app
