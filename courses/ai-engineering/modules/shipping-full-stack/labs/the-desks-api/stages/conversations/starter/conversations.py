"""The desk's conversations: each one's messages, kept in memory and served over HTTP, with every
error the app gives as a problem details object (RFC 9457)."""

from collections.abc import Mapping
from typing import Any, Literal

from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

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

    page: Page | None = None


class Conversations:
    """Every conversation, by its id, in memory."""

    def __init__(self) -> None:
        self.held: dict[str, Conversation] = {}

    def start(self, page: Page | None) -> Conversation:
        """A new conversation, with an id no one can guess."""
        raise NotImplementedError

    def get(self, conversation_id: str) -> Conversation | None:
        raise NotImplementedError

    def add(self, conversation_id: str, message: Message) -> None:
        raise NotImplementedError


def problem(
    status: int,
    detail: str | None = None,
    headers: Mapping[str, str] | None = None,
    **extensions: Any,
) -> JSONResponse:
    """A problem details response for the status: its type about:blank, its title the status's
    phrase, the detail if any, and any extensions."""
    raise NotImplementedError


def pointer(location: tuple[int | str, ...]) -> str:
    """Where in the request's body a validation error is, as a JSON Pointer in a URI fragment."""
    raise NotImplementedError


def install(app: FastAPI) -> None:
    """Gives every HTTP error and every request that doesn't fit as a problem details object."""
    raise NotImplementedError


router = APIRouter()


def held(request: Request) -> Conversations:
    """The app's conversations."""
    return request.app.state.conversations
