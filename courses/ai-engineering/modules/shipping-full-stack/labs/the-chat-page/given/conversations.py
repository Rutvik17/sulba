"""The desk's conversations: each one's messages, served over HTTP to the person who started it
alone, with every error the app gives as a problem details object (RFC 9457)."""

from collections.abc import Mapping
from datetime import datetime
from http import HTTPStatus
from typing import Any, Literal, Protocol

from fastapi import APIRouter, Depends, FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict
from starlette.exceptions import HTTPException

from sessions import Account, signed_in

Page = Literal["ssa", "va", "studentaid", "dmv"]


class Message(BaseModel):
    """A message of the conversation: the caller's, or the desk's reply."""

    role: Literal["caller", "desk"]
    content: str


class Conversation(BaseModel):
    """A conversation: its id, the help pages it was opened from, if any, and its messages."""

    id: str
    page: Page | None
    messages: list[Message]


class Summary(BaseModel):
    """A conversation in a list: its id, its help pages, if any, and when it started."""

    id: str
    page: Page | None
    started_at: datetime


class Start(BaseModel):
    """What starting a conversation takes: the help pages it's opened from, if any."""

    model_config = ConfigDict(extra="forbid")

    page: Page | None = None


class Conversations(Protocol):
    """Where the conversations are kept, each one its owner's."""

    def start(self, page: Page | None, owner: int) -> Conversation: ...

    def get(self, conversation_id: str, owner: int) -> Conversation | None: ...

    def mine(self, owner: int, limit: int = 20) -> list[Summary]: ...


def problem(
    status: int,
    detail: str | None = None,
    headers: Mapping[str, str] | None = None,
    **extensions: Any,
) -> JSONResponse:
    """A problem details response for the status: its type about:blank, its title the status's
    phrase, the detail if any, and any extensions."""
    body: dict[str, Any] = {
        "type": "about:blank",
        "title": HTTPStatus(status).phrase,
        "status": status,
    }
    if detail is not None:
        body["detail"] = detail
    return JSONResponse(
        body | extensions,
        status_code=status,
        headers=dict(headers or {}),
        media_type="application/problem+json",
    )


def pointer(location: tuple[int | str, ...]) -> str:
    """Where in the request's body a validation error is, as a JSON Pointer in a URI fragment."""
    parts = [str(part).replace("~", "~0").replace("/", "~1") for part in location[1:]]
    return "#" + "".join(f"/{part}" for part in parts)


def install(app: FastAPI) -> None:
    """Gives every HTTP error and every request that doesn't fit as a problem details object."""

    async def http_error(request: Request, error: Exception) -> JSONResponse:
        assert isinstance(error, HTTPException)
        phrase = HTTPStatus(error.status_code).phrase
        detail = None if error.detail == phrase else error.detail
        return problem(error.status_code, detail, error.headers)

    async def unfit(request: Request, error: Exception) -> JSONResponse:
        assert isinstance(error, RequestValidationError)
        errors = [
            {"detail": each["msg"], "pointer": pointer(each["loc"])}
            for each in error.errors()
        ]
        return problem(422, "The request's content doesn't fit.", errors=errors)

    app.add_exception_handler(HTTPException, http_error)
    app.add_exception_handler(RequestValidationError, unfit)


router = APIRouter()


def held(request: Request) -> Conversations:
    """The app's conversations."""
    return request.app.state.conversations


@router.post("/conversations", status_code=201)
def start(
    start: Start,
    response: Response,
    person: Account = Depends(signed_in),
    conversations: Conversations = Depends(held),
) -> Conversation:
    conversation = conversations.start(start.page, person.id)
    response.headers["Location"] = f"/conversations/{conversation.id}"
    return conversation


@router.get("/conversations")
def mine(
    person: Account = Depends(signed_in),
    conversations: Conversations = Depends(held),
) -> list[Summary]:
    """The person's conversations, the newest first."""
    return conversations.mine(person.id)


@router.get("/conversations/{conversation_id}")
def get(
    conversation_id: str,
    person: Account = Depends(signed_in),
    conversations: Conversations = Depends(held),
) -> Conversation:
    # Someone else's conversation is as missing as one that never was.
    conversation = conversations.get(conversation_id, person.id)
    if conversation is None:
        raise HTTPException(404, "There's no conversation with this id.")
    return conversation
