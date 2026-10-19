"""The shop's assistant's requests, asked again when a failure may pass, within a deadline."""

import asyncio
import random
from collections.abc import Callable

import httpx

from chat import MODEL, ModelError, Reply


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
    raise NotImplementedError
