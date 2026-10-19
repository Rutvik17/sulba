"""Asks the model for JSON that matches a schema, and asks again with what was wrong."""

import json
from typing import Any

import httpx

from schema import errors

MODEL = "Qwen3.5-0.8B"
AGAIN = "Reply again with only the corrected JSON."


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
    sent = list(messages)
    problems: list[str] = []
    for _ in range(attempts):
        body = {
            "model": MODEL,
            "messages": sent,
            "max_completion_tokens": max_tokens,
            "response_format": {
                "type": "json_schema",
                "json_schema": {"name": name, "schema": schema, "strict": True},
            },
        }
        response = client.post("/chat/completions", json=body)
        if response.is_error:
            raise ModelError(response.status_code, error_message(response))
        choice = response.json()["choices"][0]
        text = choice["message"]["content"] or ""
        value, problems = read(text, choice["finish_reason"], schema)
        if not problems:
            return value
        feedback = "\n".join(
            [
                "Your reply doesn't match the schema:",
                *(f"- {each}" for each in problems),
                AGAIN,
            ]
        )
        sent = [
            *sent,
            {"role": "assistant", "content": text},
            {"role": "user", "content": feedback},
        ]
    raise NoMatch(problems)


def error_message(response: httpx.Response) -> str:
    """The message of the error in the response's JSON, or the response's text when it has
    none."""
    try:
        return response.json()["error"]["message"]
    except ValueError, KeyError, TypeError:
        return response.text


def read(
    text: str, finish_reason: str, schema: dict[str, Any]
) -> tuple[Any, list[str]]:
    """The value a reply holds, and what's wrong with it: nothing when it matches."""
    if finish_reason == "length":
        return None, ["The reply was cut off at its token limit."]
    try:
        value = json.loads(text)
    except json.JSONDecodeError as error:
        return None, [f"The reply isn't JSON: {error}"]
    return value, [f"{error.path}: {error.message}" for error in errors(value, schema)]
