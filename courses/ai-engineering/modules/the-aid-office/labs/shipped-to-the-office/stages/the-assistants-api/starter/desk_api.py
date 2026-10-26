"""The office's desk, all in one module: its settings, the college's sign-in, each question
answered as the model writes it, and a log of the questions asked.

    uv run uvicorn desk_api:create_app --factory
"""

import json
import logging
import os
from collections.abc import AsyncIterator, Iterator, Mapping
from contextlib import asynccontextmanager
from dataclasses import asdict
from typing import Literal

import httpx
from desk import NO_RECORD, SIGN_IN, STAFF_SIGNED_OUT
from desk_auth import Registration
from desk_auth import router as auth_router
from fastapi import Depends, FastAPI, Request
from fastapi.responses import StreamingResponse
from migrations import migrate
from pgvector.psycopg import register_vector
from psycopg_pool import ConnectionPool
from pydantic import BaseModel, Field, SecretStr, ValidationError
from records import lines, record
from sessions import SESSION_COOKIE, SESSION_MIGRATIONS, Sessions
from sign_in import discover
from starlette.exceptions import HTTPException
from streamed import Piece, Verdict, stream
from tokens import Keys

# Each setting's environment variable, and its value when the variable isn't set, if it has one.
VARIABLES = {
    "model_url": ("OFFICE_MODEL_URL", "http://127.0.0.1:9931/v1"),
    "database_url": ("OFFICE_DATABASE_URL", None),
    "issuer": ("OFFICE_ISSUER", None),
    "client_id": ("OFFICE_CLIENT_ID", None),
    "client_secret": ("OFFICE_CLIENT_SECRET", None),
    "public_url": ("OFFICE_PUBLIC_URL", "http://127.0.0.1:8000"),
}
# The methods that change nothing, which a request from another site may use.
SAFE = {"GET", "HEAD", "OPTIONS"}
NOT_A_STUDENT = "The desk answers Harbor College's students."

log = logging.getLogger("desk")


class Settings(BaseModel):
    """Where the model answers and the database is, the college's provider that signs people
    in, the desk's id and secret there, and the address the desk is served at, with no path."""

    model_url: str = Field(pattern=r"^https?://")
    database_url: str = Field(pattern=r"^postgres(ql)?://")
    issuer: str = Field(pattern=r"^https://")
    client_id: str = Field(min_length=1)
    client_secret: SecretStr = Field(min_length=1)
    public_url: str = Field(pattern=r"^https?://[^/]+$")

    @property
    def registration(self) -> Registration:
        return Registration(
            client_id=self.client_id,
            client_secret=self.client_secret.get_secret_value(),
            redirect_uri=f"{self.public_url}/auth/callback",
            secure=self.public_url.startswith("https://"),
        )


class Question(BaseModel):
    """A question, and what it's about: the office's pages, or the student's own aid."""

    text: str = Field(min_length=1, max_length=1000, pattern=r"\S")
    about: Literal["pages", "my aid"] = "pages"


def settings_from(environ: Mapping[str, str]) -> Settings:
    """The settings from the environment's variables, or a ValueError that names the ones
    that are missing or don't fit."""
    given = {}
    for name, (variable, default) in VARIABLES.items():
        value = environ.get(variable, default)
        if value is not None:
            given[name] = value
    try:
        return Settings(**given)
    except ValidationError as error:
        wrong = [VARIABLES[str(each["loc"][0])][0] for each in error.errors()]
        raise ValueError(f"These settings don't fit: {', '.join(wrong)}.") from error


def event(name: str, data: dict) -> str:
    return f"event: {name}\ndata: {json.dumps(data)}\n\n"


def create_app(
    settings: Settings | None = None,
    client: httpx.Client | None = None,
    identity: httpx.AsyncClient | None = None,
) -> FastAPI:
    """The desk, with the settings given, or those of the environment, and the client given to
    the model and the one given to the provider, or ones it makes and closes as it stops."""
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
        model = client or httpx.Client(base_url=chosen.model_url)
        provider_client = identity or httpx.AsyncClient(timeout=10)
        pool = ConnectionPool(
            chosen.database_url,
            min_size=1,
            max_size=8,
            kwargs={"autocommit": True},
            configure=register_vector,
            open=False,
        )
        try:
            pool.open(wait=True, timeout=10)
            with pool.connection() as conn:
                migrate(conn, SESSION_MIGRATIONS)
            provider = await discover(provider_client, chosen.issuer)
            app.state.model = model
            app.state.pool = pool
            app.state.sessions = Sessions(pool)
            app.state.registration = chosen.registration
            app.state.provider = provider
            app.state.keys = Keys(provider_client, provider)
            yield
        finally:
            pool.close()
            if client is None:
                model.close()
            if identity is None:
                await provider_client.aclose()

    app = FastAPI(
        title="Harbor College's aid desk",
        lifespan=lifespan,
        dependencies=[Depends(from_this_site)],
    )
    app.include_router(auth_router)

    def student(request: Request) -> str | None:
        """The student signed in, by the email the college gives them, or None for a visitor.
        Someone signed in whom the office's directory doesn't list is refused."""
        token = request.cookies.get(SESSION_COOKIE)
        account = request.app.state.sessions.find(token) if token else None
        if account is None:
            return None
        with request.app.state.pool.connection() as conn:
            found = conn.execute(
                "SELECT student FROM directory WHERE email = %s", [account.email]
            ).fetchone()
        if found is None:
            raise HTTPException(403, NOT_A_STUDENT)
        return found[0]

    def answered(
        request: Request, who: str | None, question: Question
    ) -> Iterator[str]:
        state = request.app.state
        # Staff can look a student up with ?student=.
        student = request.query_params.get("student", who)
        log.info("Question from %s: %s", student, question.text)
        with state.pool.connection() as conn:
            if question.about == "my aid":
                if student is None:
                    verdict = Verdict(SIGN_IN, [], False)
                elif (found := record(conn, student)) is None:
                    verdict = Verdict(NO_RECORD, [], False)
                else:
                    verdict = Verdict("\n".join(lines(found)), [], False)
                yield event("verdict", asdict(verdict))
                return
            for each in stream(conn, state.model, question.text):
                if isinstance(each, Piece):
                    yield event("piece", {"text": each.text})
                    continue
                if each.to_staff:
                    conn.execute(
                        "INSERT INTO tickets (student, question) VALUES (%s, %s)",
                        [student, question.text],
                    )
                    if student is None:
                        each = Verdict(STAFF_SIGNED_OUT, [], True)
                else:
                    yield event("verdict", asdict(each))

    @app.post("/questions")
    def ask(
        question: Question, request: Request, who: str | None = Depends(student)
    ) -> StreamingResponse:
        """The answer as it comes: a piece event for each piece of its text, then a verdict
        event, which takes the pieces' place."""
        return StreamingResponse(
            answered(request, who, question), media_type="text/event-stream"
        )

    @app.get("/health")
    def health() -> dict[str, str]:
        """Whether the desk is up, without asking the model or the database anything."""
        return {"status": "ok"}

    return app
