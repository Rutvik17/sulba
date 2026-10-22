"""The desk's app on Postgres: its settings from the environment, the database migrated as the
app starts, conversations and turns kept there, and each day's usage for the dashboard.

    uv run uvicorn app:create_app --factory
"""

from collections.abc import Mapping
from datetime import date
from pathlib import Path

import httpx
from fastapi import FastAPI
from pydantic import BaseModel, Field

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
    raise NotImplementedError


def create_app(
    settings: Settings | None = None,
    data: Path = Path("data"),
    client: httpx.AsyncClient | None = None,
) -> FastAPI:
    """The app, with the settings given, or those of the environment, the help pages in data,
    and the client given to the model, or one it makes from the settings and closes as it
    stops."""
    raise NotImplementedError
