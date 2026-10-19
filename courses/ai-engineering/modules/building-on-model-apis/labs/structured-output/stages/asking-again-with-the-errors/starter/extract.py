"""Asks the model for JSON that matches a schema, and asks again with what was wrong."""

from typing import Any

import httpx

MODEL = "Qwen3.5-0.8B"


class ModelError(Exception):
    """An error the API answered with: its HTTP status and its message."""

    def __init__(self, status: int, message: str) -> None:
        super().__init__(f"{status}: {message}")
        self.status = status
        self.message = message


class NoMatch(Exception):
    """None of the model's replies matched the schema. problems says what was wrong with the
    last."""

    def __init__(self, problems: list[str]) -> None:
        super().__init__("; ".join(problems))
        self.problems = problems


def ask_for(
    client: httpx.Client,
    messages: list[dict[str, str]],
    schema: dict[str, Any],
    name: str,
    attempts: int = 3,
    max_tokens: int = 512,
) -> Any:
    """The JSON value the model replies to messages with, matching schema. Each reply that
    doesn't goes back to the model with what's wrong with it, up to attempts requests in all.
    Raises NoMatch when none matches, and ModelError when the API answers with an error."""
    raise NotImplementedError


def error_message(response: httpx.Response) -> str:
    """The message of the error in the response's JSON, or the response's text when it has
    none."""
    try:
        return response.json()["error"]["message"]
    except ValueError, KeyError, TypeError:
        return response.text
