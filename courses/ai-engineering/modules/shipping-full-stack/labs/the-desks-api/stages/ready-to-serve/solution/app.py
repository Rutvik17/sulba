"""The desk's app, ready to serve: its settings from the environment, one client to the model
and one search over the help pages for every request, opened as the app starts and closed as it
stops, the conversations' and replies' routes, and a health check.

    uv run uvicorn app:create_app --factory
"""

import os
from collections.abc import AsyncIterator, Mapping
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import FastAPI
from pydantic import BaseModel, Field, ValidationError

from agent import Agent
from conversations import Conversations, install
from conversations import router as conversations_router
from desk import TICKETS, Actions, Desk, free_times, load_search
from gate import Gate
from replies import Agents
from replies import router as replies_router

# Each setting's environment variable, and its value when the variable isn't set.
VARIABLES = {
    "model_url": ("DESK_MODEL_URL", "http://127.0.0.1:9931/v1"),
    "running": ("DESK_RUNNING", "1"),
    "waiting": ("DESK_WAITING", "8"),
    "seconds": ("DESK_SECONDS", "120"),
}


class Settings(BaseModel):
    """Where the model answers, how many replies run and wait at once, and each one's limit."""

    model_url: str = Field(pattern=r"^https?://")
    running: int = Field(ge=1)
    waiting: int = Field(ge=0)
    seconds: float = Field(gt=0)


def settings_from(environ: Mapping[str, str]) -> Settings:
    """The settings from the environment's variables, each one's default where it isn't set. A
    value that doesn't fit raises ValueError, naming every variable that's wrong."""
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
        try:
            desk = Desk(load_search(model, data), TICKETS, free_times())
            app.state.client = model
            app.state.desk = desk
            app.state.conversations = Conversations()
            app.state.gate = Gate(chosen.running, chosen.waiting, chosen.seconds)
            app.state.agents = Agents(lambda page: Agent(model, Actions(desk), page))
            yield
        finally:
            if client is None:
                await model.aclose()

    app = FastAPI(title="The help desk", lifespan=lifespan)
    install(app)
    app.include_router(conversations_router)
    app.include_router(replies_router)

    @app.get("/health")
    def health() -> dict[str, str]:
        """Whether the app is up, without asking the model anything."""
        return {"status": "ok"}

    return app
