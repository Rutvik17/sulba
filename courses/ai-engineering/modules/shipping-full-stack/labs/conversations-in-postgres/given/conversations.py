"""The desk's conversations: each one's messages, kept in memory and served over HTTP, with every
error the app gives as a problem details object (RFC 9457)."""

import secrets
from collections.abc import Mapping
from http import HTTPStatus
from typing import Any, Literal

from fastapi import APIRouter, Depends, FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict
from starlette.exceptions import HTTPException

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


class Start(BaseModel):
    """What starting a conversation takes: the help pages it's opened from, if any."""

    model_config = ConfigDict(extra="forbid")

    page: Page | None = None


class Conversations:
    """Every conversation, by its id, in memory."""

    def __init__(self) -> None:
        self.held: dict[str, Conversation] = {}

    def start(self, page: Page | None) -> Conversation:
        """A new conversation, with an id no one can guess."""
        conversation = Conversation(
            id=secrets.token_urlsafe(16), page=page, messages=[]
        )
        self.held[conversation.id] = conversation
        return conversation

    def get(self, conversation_id: str) -> Conversation | None:
        return self.held.get(conversation_id)

    def add(self, conversation_id: str, message: Message) -> None:
        self.held[conversation_id].messages.append(message)


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
    start: Start, response: Response, conversations: Conversations = Depends(held)
) -> Conversation:
    conversation = conversations.start(start.page)
    response.headers["Location"] = f"/conversations/{conversation.id}"
    return conversation


@router.get("/conversations/{conversation_id}")
def get(
    conversation_id: str, conversations: Conversations = Depends(held)
) -> Conversation:
    conversation = conversations.get(conversation_id)
    if conversation is None:
        raise HTTPException(404, "There's no conversation with this id.")
    return conversation
