"""The shop's assistant with tools: it runs the tools the model calls, and asks again with what
they returned, until the model answers."""

from collections.abc import Callable
from typing import Any

import httpx

from tools import describe, run

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
    tools = [describe(function) for function in functions]
    named = {function.__name__: function for function in functions}
    sent = list(messages)
    for _ in range(rounds):
        body = {
            "model": MODEL,
            "messages": sent,
            "tools": tools,
            "max_completion_tokens": max_tokens,
        }
        response = client.post("/chat/completions", json=body)
        if response.is_error:
            raise ModelError(response.status_code, error_message(response))
        choice = response.json()["choices"][0]
        message, finish_reason = choice["message"], choice["finish_reason"]
        if finish_reason == "stop":
            return message["content"] or ""
        if finish_reason != "tool_calls":
            raise NoAnswer(f"The reply stopped for {finish_reason!r}.")
        sent.append(
            {
                "role": "assistant",
                "content": message["content"],
                "tool_calls": message["tool_calls"],
            }
        )
        sent += [run(named, call) for call in message["tool_calls"]]
    raise NoAnswer(f"The model still called tools after {rounds} requests.")


def error_message(response: httpx.Response) -> str:
    """The message of the error in the response's JSON, or the response's text when it has
    none."""
    try:
        return response.json()["error"]["message"]
    except ValueError, KeyError, TypeError:
        return response.text
