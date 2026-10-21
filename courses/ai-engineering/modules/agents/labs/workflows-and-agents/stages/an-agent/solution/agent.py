"""The desk as an agent: the model reads the whole conversation and the desk's tools, and calls
them as it sees fit until it replies to the caller."""

import time
from dataclasses import dataclass
from typing import Any

import httpx

from desk import SERVICES, Desk, tools
from workflow import MODEL, SAMPLING

SYSTEM = (
    "You are the assistant of a help desk for four US public services: Social Security (ssa), "
    "veterans' benefits (va), federal student aid (studentaid) and New York State's DMV (dmv). "
    "The caller is signed in, and the tools act on their account. Today is Friday 30 October "
    "2026. Advisers call back on Monday 2026-11-02, Tuesday 2026-11-03, Wednesday 2026-11-04, "
    "Thursday 2026-11-05 and Friday 2026-11-06, on the hour from 09:00 to 16:00; morning is "
    "before 12:00.\n\n"
    "- Answer questions about the services from their help pages: search them, and cite each "
    "passage you use by its id in square brackets, like [p17]. If the pages don't answer, say "
    "so.\n"
    "- A question about the caller's own case needs an adviser: offer to open a ticket for its "
    "service.\n"
    "- A callback is booked for one of the caller's open tickets, at a time its service's "
    "advisers are free.\n"
    "- Before you open a ticket or book a callback, tell the caller exactly what you'll do and "
    "ask them to confirm. Do it only once they say yes.\n"
    "- If you can't tell what the caller wants, ask them."
)


@dataclass(frozen=True)
class Request:
    """One request the agent sent: its tokens of prompt and of reply, the seconds it took, why
    the reply finished, and the tools it called."""

    prompt_tokens: int
    completion_tokens: int
    seconds: float
    finish: str
    calls: tuple[str, ...]


class OutOfRounds(Exception):
    """The model still called tools after the requests a turn may take."""


class Agent:
    """One conversation with the caller, through the desk, from the help pages the chat was
    opened from, or None for the desk's home page. A turn takes at most rounds requests."""

    def __init__(
        self,
        client: httpx.Client,
        desk: Desk,
        page: str | None,
        rounds: int = 8,
        max_tokens: int = 768,
    ) -> None:
        self.client = client
        self.desk = desk
        self.rounds = rounds
        self.max_tokens = max_tokens
        opened = (
            f"The caller opened the chat on the {SERVICES[page]} pages."
            if page
            else "The caller opened the chat on the help desk's home page."
        )
        self.messages: list[dict[str, Any]] = [
            {"role": "system", "content": f"{SYSTEM}\n\n{opened}"}
        ]
        self.requests: list[Request] = []
        self.turns = 0

    def reply(self, message: str) -> str:
        """The desk's reply to the caller's next message, once the tools the model calls have
        run. Raises OutOfRounds when the model still calls tools after rounds requests."""
        self.desk.turn = self.turns
        self.turns += 1
        self.messages.append({"role": "user", "content": message})
        for _ in range(self.rounds):
            body = {
                "model": MODEL,
                "messages": self.messages,
                "tools": tools(),
                "max_tokens": self.max_tokens,
                **SAMPLING,
            }
            began = time.perf_counter()
            response = self.client.post("/chat/completions", json=body)
            seconds = time.perf_counter() - began
            response.raise_for_status()
            answer = response.json()
            choice = answer["choices"][0]
            said, calls = choice["message"], choice["message"].get("tool_calls") or []
            usage = answer.get("usage") or {}
            self.requests.append(
                Request(
                    usage.get("prompt_tokens", 0),
                    usage.get("completion_tokens", 0),
                    seconds,
                    choice["finish_reason"],
                    tuple(call["function"]["name"] for call in calls),
                )
            )
            kept: dict[str, Any] = {"role": "assistant", "content": said.get("content")}
            if calls:
                kept["tool_calls"] = calls
            self.messages.append(kept)
            if not calls:
                return said.get("content") or ""
            for call in calls:
                result = self.desk.call(
                    call["function"]["name"], call["function"]["arguments"]
                )
                self.messages.append(
                    {"role": "tool", "tool_call_id": call["id"], "content": result}
                )
        raise OutOfRounds(f"The model still called tools after {self.rounds} requests.")
