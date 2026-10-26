from collections.abc import Mapping

import httpx
from fastapi import FastAPI
from pydantic import BaseModel, SecretStr

# Each setting's environment variable, and its value when the variable isn't set, if it has one.
VARIABLES = {
    "model_url": ("OFFICE_MODEL_URL", "http://127.0.0.1:9931/v1"),
    "database_url": ("OFFICE_DATABASE_URL", None),
    "issuer": ("OFFICE_ISSUER", None),
    "client_id": ("OFFICE_CLIENT_ID", None),
    "client_secret": ("OFFICE_CLIENT_SECRET", None),
    "public_url": ("OFFICE_PUBLIC_URL", "http://127.0.0.1:8000"),
}
NOT_A_STUDENT = "The desk answers Harbor College's students."


class Settings(BaseModel):
    model_url: str
    database_url: str
    issuer: str
    client_id: str
    client_secret: SecretStr
    public_url: str


def settings_from(environ: Mapping[str, str]) -> Settings:
    raise NotImplementedError


def create_app(
    settings: Settings | None = None,
    client: httpx.Client | None = None,
    identity: httpx.AsyncClient | None = None,
) -> FastAPI:
    raise NotImplementedError
