"""The desk's app, ready to serve: its settings from the environment, one client to the model
and one search over the help pages for every request, opened as the app starts and closed as it
stops, the conversations' and replies' routes, and a health check.

    uv run uvicorn app:create_app --factory
"""

from collections.abc import Mapping
from pathlib import Path

import httpx
from fastapi import FastAPI
from pydantic import BaseModel, Field

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
