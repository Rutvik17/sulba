"""The desk as an agent on tools written for the model: it searches, reads and proposes as it
sees fit, and the desk makes a proposal only once the caller says yes."""

import time
from dataclasses import dataclass
from typing import Any

import httpx

from actions import Actions, tools
from desk import SERVICES, Desk

MODEL = "Qwen3.5-4B"
# The sampling settings Qwen3.5-4B's model card gives for its non-thinking mode.
SAMPLING = {
    "temperature": 0.7,
    "top_p": 0.8,
    "top_k": 20,
    "min_p": 0.0,
    "presence_penalty": 1.5,
}
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
    "- A question about the caller's own case needs an adviser: propose a ticket for its "
    "service.\n"
    "- To arrange a call from an adviser, propose a callback.\n"
    "- A proposal waits for the caller: tell them what it will do and ask them to confirm. The "
    "desk does it when they say yes, and tells you what it did.\n"
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
        self.actions = Actions(desk)
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
        """The desk's reply to the caller's next message. A yes makes the proposal waiting for
        it before the model reads the message, which then carries what the desk did."""
        raise NotImplementedError
