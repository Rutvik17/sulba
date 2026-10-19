"""The shop's assistant's requests, asked again when a failure may pass, within a deadline."""

import asyncio
import random
from collections.abc import Callable
from typing import Any

import httpx

from chat import MODEL, ModelError, Reply

# The statuses whose request may succeed when it's sent again, besides every 5xx.
RETRIED = {408, 409, 429}
# Failures of the connection rather than the request, which may pass too.
TRANSIENT = (httpx.TimeoutException, httpx.NetworkError, httpx.RemoteProtocolError)


class GaveUp(Exception):
    """The model gave no answer before the deadline. Its cause is the last failure."""


async def ask_within(
    client: httpx.AsyncClient,
    messages: list[dict[str, str]],
    max_tokens: int,
    deadline: float,
    timeout: float = 20,
    jitter: Callable[[], float] = random.random,
) -> Reply:
    """The model's reply to messages, asking again after each failure that may pass, until
    deadline seconds after the call. Each attempt waits at most timeout seconds for its reply.
    Raises ModelError for an error that can't pass, and GaveUp when the time runs out."""
    loop = asyncio.get_running_loop()
    end = loop.time() + deadline
    body = {"model": MODEL, "messages": messages, "max_completion_tokens": max_tokens}
    attempt = 0
    while True:
        attempt += 1
        wait = None
        try:
            left = min(timeout, end - loop.time())
            response = await client.post("/chat/completions", json=body, timeout=left)
        except TRANSIENT as error:
            failure: Exception = error
        else:
            if not response.is_error:
                return reply_of(response.json())
            failure = ModelError(response.status_code, message_of(response))
            if response.status_code not in RETRIED and response.status_code < 500:
                raise failure
            wait = retry_after(response)
        if wait is None:
            wait = min(2 ** (attempt - 1), 8) * (0.5 + jitter() / 2)
        if loop.time() + wait >= end:
            raise GaveUp(f"No answer within {deadline} seconds.") from failure
        await asyncio.sleep(wait)


def reply_of(reply: dict[str, Any]) -> Reply:
    choice, usage = reply["choices"][0], reply["usage"]
    return Reply(
        text=choice["message"]["content"] or "",
        finish_reason=choice["finish_reason"],
        prompt_tokens=usage["prompt_tokens"],
        completion_tokens=usage["completion_tokens"],
    )


def message_of(response: httpx.Response) -> str:
    """The message of the error in the response's JSON, or the response's text when it has
    none."""
    try:
        return response.json()["error"]["message"]
    except ValueError, KeyError, TypeError:
        return response.text


def retry_after(response: httpx.Response) -> int | None:
    """The seconds the response's Retry-After header asks the client to wait, or None when it
    gives none."""
    value = response.headers.get("retry-after", "")
    return int(value) if value.isdigit() else None
