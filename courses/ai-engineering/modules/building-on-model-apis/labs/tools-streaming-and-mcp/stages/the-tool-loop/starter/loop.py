"""The shop's assistant with tools: it runs the tools the model calls, and asks again with what
they returned, until the model answers."""

from collections.abc import Callable
from typing import Any

import httpx

MODEL = "Qwen3.5-0.8B"


class ModelError(Exception):
    """An error the API answered with: its HTTP status and its message."""

    def __init__(self, status: int, message: str) -> None:
        super().__init__(f"{status}: {message}")
        self.status = status
        self.message = message


class NoAnswer(Exception):
    """The model gave no answer: it kept calling tools, or its reply was cut off."""


def answer(
    client: httpx.Client,
    messages: list[dict[str, Any]],
    functions: list[Callable[..., Any]],
    rounds: int = 4,
    max_tokens: int = 512,
) -> str:
    """The model's answer to messages, once the tools it calls have run. Raises NoAnswer when it
    still calls tools after rounds requests, or when its reply is cut off."""
    raise NotImplementedError


def error_message(response: httpx.Response) -> str:
    """The message of the error in the response's JSON, or the response's text when it has
    none."""
    try:
        return response.json()["error"]["message"]
    except ValueError, KeyError, TypeError:
        return response.text
