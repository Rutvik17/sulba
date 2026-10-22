"""The desk's app, signed in: its settings from the environment, the provider found and the
database migrated as the app starts, each person's conversations theirs alone, each day's usage
for the dashboard, and requests from other sites refused.

    uv run uvicorn app:create_app --factory
"""

import os
from collections.abc import AsyncIterator, Mapping
from contextlib import asynccontextmanager
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import httpx
from fastapi import Depends, FastAPI, Query, Request
from psycopg_pool import ConnectionPool
from pydantic import BaseModel, Field, SecretStr, ValidationError
from starlette.exceptions import HTTPException

from agent import Agent
from conversations import install
from conversations import router as conversations_router
from desk import TICKETS, Actions, Desk, free_times, load_search
from desk_auth import Registration
from desk_auth import router as auth_router
from gate import Gate
from migrations import MIGRATIONS, migrate
from replies import Agents
from replies import router as replies_router
from sessions import SESSION_MIGRATIONS, Account, Sessions, signed_in
from sign_in import discover
from store import OWNERS, Store
from tokens import Keys

# Each setting's environment variable, and its value when the variable isn't set, if it has one.
VARIABLES = {
    "model_url": ("DESK_MODEL_URL", "http://127.0.0.1:9931/v1"),
    "database_url": ("DESK_DATABASE_URL", None),
    "running": ("DESK_RUNNING", "1"),
    "waiting": ("DESK_WAITING", "8"),
    "seconds": ("DESK_SECONDS", "120"),
    "issuer": ("DESK_ISSUER", None),
    "client_id": ("DESK_CLIENT_ID", None),
    "client_secret": ("DESK_CLIENT_SECRET", None),
    "public_url": ("DESK_PUBLIC_URL", "http://127.0.0.1:8000"),
}

# The methods that change nothing, which a request from another site may use.
SAFE = {"GET", "HEAD", "OPTIONS"}


class Settings(BaseModel):
    """Where the model answers and the database is, how many replies run and wait at once, and
    each one's limit; the provider that signs people in, and the desk's id and secret there;
    and the address the desk is served at, with no path."""

    model_url: str = Field(pattern=r"^https?://")
    database_url: str = Field(pattern=r"^postgres(ql)?://")
    running: int = Field(ge=1)
    waiting: int = Field(ge=0)
    seconds: float = Field(gt=0)
    issuer: str = Field(pattern=r"^https://")
    client_id: str = Field(min_length=1)
    client_secret: SecretStr = Field(min_length=1)
    public_url: str = Field(pattern=r"^https?://[^/]+$")

    @property
    def registration(self) -> Registration:
        """The desk as the provider knows it. Its cookies go only over HTTPS when it's served
        over HTTPS."""
        return Registration(
            client_id=self.client_id,
            client_secret=self.client_secret.get_secret_value(),
            redirect_uri=f"{self.public_url}/auth/callback",
            secure=self.public_url.startswith("https://"),
        )


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
    identity: httpx.AsyncClient | None = None,
) -> FastAPI:
    """The app, with the settings given, or those of the environment, the help pages in data,
    the client given to the model and the one given to the provider, or ones it makes and
    closes as it stops."""
    chosen = settings or settings_from(os.environ)

    async def from_this_site(request: Request) -> None:
        """Refuses a request from another site that would change something: its browser says
        so in Sec-Fetch-Site or, where it sends no Sec-Fetch-Site, in Origin."""
        if request.method in SAFE:
            return
        site = request.headers.get("sec-fetch-site")
        origin = request.headers.get("origin")
        if site is not None:
            elsewhere = site != "same-origin"
        else:
            elsewhere = origin is not None and origin != chosen.public_url
        if elsewhere:
            raise HTTPException(
                403, "A request from another site can't change anything."
            )

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        # A reply can take as long as its limit, so the client waits that long for each read.
        timeout = httpx.Timeout(chosen.seconds, connect=10)
        model = client or httpx.AsyncClient(base_url=chosen.model_url, timeout=timeout)
        provider_client = identity or httpx.AsyncClient(timeout=10)
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
                migrate(conn, [*MIGRATIONS, *SESSION_MIGRATIONS, OWNERS])
            provider = await discover(provider_client, chosen.issuer)
            desk = Desk(load_search(model, data), TICKETS, free_times())
            app.state.client = model
            app.state.pool = pool
            app.state.desk = desk
            app.state.conversations = Store(pool)
            app.state.sessions = Sessions(pool)
            app.state.registration = chosen.registration
            app.state.provider = provider
            app.state.keys = Keys(provider_client, provider)
            app.state.gate = Gate(chosen.running, chosen.waiting, chosen.seconds)
            app.state.agents = Agents(lambda page: Agent(model, Actions(desk), page))
            yield
        finally:
            pool.close()
            if client is None:
                await model.aclose()
            if identity is None:
                await provider_client.aclose()

    app = FastAPI(
        title="The help desk",
        lifespan=lifespan,
        dependencies=[Depends(from_this_site)],
    )
    install(app)
    app.include_router(auth_router)
    app.include_router(conversations_router)
    app.include_router(replies_router)

    @app.get("/health")
    def health() -> dict[str, str]:
        """Whether the app is up, without asking the model or the database anything."""
        return {"status": "ok"}

    @app.get("/me")
    def me(person: Account = Depends(signed_in)) -> Account:
        """The person signed in."""
        return person

    @app.get("/usage")
    def usage(
        request: Request,
        days: int = Query(7, ge=1, le=90),
        person: Account = Depends(signed_in),
    ) -> list[Day]:
        """Each of the last days' usage of the person's conversations, today's included, for
        the days with turns."""
        since = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        since -= timedelta(days=days - 1)
        pool: ConnectionPool = request.app.state.pool
        with pool.connection() as conn:
            # started_at itself is compared, so the index on it finds the days' turns.
            rows = conn.execute(
                """
                SELECT (turns.started_at AT TIME ZONE 'UTC')::date AS day,
                    count(*),
                    count(*) FILTER (WHERE outcome = 'done'),
                    sum(prompt_tokens),
                    sum(completion_tokens),
                    percentile_cont(0.5) WITHIN GROUP (ORDER BY seconds),
                    percentile_cont(0.9) WITHIN GROUP (ORDER BY seconds)
                FROM turns
                JOIN conversations ON conversations.id = turns.conversation_id
                WHERE conversations.owner = %s AND turns.started_at >= %s
                GROUP BY day
                ORDER BY day
                """,
                [person.id, since],
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
