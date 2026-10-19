"""Reads a model's reply as it streams in: its text as it comes, and its tool calls once each is
whole."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import httpx

MODEL = "Qwen3.5-0.8B"


class ModelError(Exception):
    """An error the API answered with: its HTTP status and its message."""

    def __init__(self, status: int, message: str) -> None:
        super().__init__(f"{status}: {message}")
        self.status = status
        self.message = message


@dataclass(frozen=True)
class Streamed:
    """A streamed reply, put back together: its text, its tool calls as a whole reply has them,
    why it finished, and the tokens it used."""

    text: str
    tool_calls: list[dict[str, Any]]
    finish_reason: str
    usage: dict[str, int] | None


def stream(
    client: httpx.Client,
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]] | None = None,
    on_text: Callable[[str], None] = lambda piece: None,
) -> Streamed:
    """Asks for a streamed reply to messages, hands each piece of its text to on_text as it
    arrives, and returns the whole reply."""
    raise NotImplementedError


def error_message(response: httpx.Response) -> str:
    """The message of the error in the response's JSON, or the response's text when it has
    none."""
    try:
        return response.json()["error"]["message"]
    except ValueError, KeyError, TypeError:
        return response.text
