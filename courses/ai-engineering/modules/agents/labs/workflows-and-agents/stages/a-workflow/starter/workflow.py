"""The desk as a workflow: the model sorts the caller's first message into a route, and code
follows a fixed path for each, with one more request to answer a question. A ticket or a
callback waits for the caller's yes."""

import json
import re
from dataclasses import dataclass
from typing import Any

import httpx

from desk import DAYS, SERVICES, TIMES, Desk

MODEL = "Qwen3.5-4B"
# The sampling settings Qwen3.5-4B's model card gives for its non-thinking mode.
SAMPLING = {
    "temperature": 0.7,
    "top_p": 0.8,
    "top_k": 20,
    "min_p": 0.0,
    "presence_penalty": 1.5,
}
DESK = (
    "You work for a help desk for four US public services: Social Security (ssa), veterans' "
    "benefits (va), federal student aid (studentaid) and New York State's DMV (dmv). Today is "
    "Friday 30 October 2026."
)
ROUTER = (
    DESK
    + " Sort the caller's message. kind is question for a question about how a service "
    "works, which its help pages answer; case when something has gone wrong or is held up "
    "with the caller's own claim, payment, application, card or record, which an adviser has "
    "to look into; callback when the caller asks for an adviser to call them; and other for "
    "anything else. service is the service it's about, or none. day is the weekday the caller "
    "wants the call, or none. part is morning, before 12:00, or afternoon, when they name "
    "one, or none. time is none unless they name an hour, such as 10:00 or 2 PM."
)
ANSWER = (
    DESK
    + " Answer the caller's question from the passages below, in a few sentences, and "
    "cite each passage you use by its id in square brackets, like [p17]. If they don't answer "
    "it, say so."
)
WEEKDAYS = {name.lower(): day for day, name in DAYS.items()}
ROUTE = {
    "type": "object",
    "properties": {
        "kind": {"type": "string", "enum": ["question", "case", "callback", "other"]},
        "service": {"type": "string", "enum": [*SERVICES, "none"]},
        "day": {"type": "string", "enum": ["none", *WEEKDAYS]},
        "part": {"type": "string", "enum": ["none", "morning", "afternoon"]},
        "time": {"type": "string", "enum": ["none", *TIMES]},
    },
    "required": ["kind", "service", "day", "part", "time"],
}
YES = re.compile(r"\s*(yes|yeah|yep|sure|ok|okay|please do|go ahead)\b", re.IGNORECASE)


@dataclass(frozen=True)
class Route:
    """What the caller's message asks for, as the model sorted it: a field it didn't give is
    None."""

    kind: str
    service: str | None = None
    day: str | None = None
    time: str | None = None
    part: str | None = None


def chat(client: httpx.Client, messages: list[dict[str, Any]], **extra: Any) -> str:
    """The model's reply to messages."""
    body = {
        "model": MODEL,
        "messages": messages,
        "max_tokens": 512,
        **SAMPLING,
        **extra,
    }
    response = client.post("/chat/completions", json=body)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"] or ""


def route(client: httpx.Client, message: str, page: str | None) -> Route:
    """The route of the caller's message, from one request whose reply follows ROUTE. A reply
    that isn't a route is the route other. A service the caller doesn't name is the page's."""
    raise NotImplementedError


class Workflow:
    """One conversation with the caller, through the desk, from the help pages the chat was
    opened from, or None for the desk's home page."""

    def __init__(self, client: httpx.Client, desk: Desk, page: str | None) -> None:
        self.client = client
        self.desk = desk
        self.page = page
        self.turns = 0
        self.pending: tuple[str, dict[str, str]] | None = None

    def reply(self, message: str, found: Route | None = None) -> str:
        """The desk's reply to the caller's next message, down the path of its route, or of
        found when the message has been sorted already."""
        raise NotImplementedError

    def follow(self, message: str, found: Route) -> str:
        """The reply down the path of the message's route."""
        raise NotImplementedError

    def answer(self, question: str, service: str | None) -> str:
        """The answer to a question, from the passages the search finds for it."""
        raise NotImplementedError

    def callback(self, message: str, found: Route) -> str:
        """The offer of a callback the route asks for, or a question when the desk can't place it."""
        raise NotImplementedError

    def ask(self) -> str:
        """A question about what the caller wants, with their open tickets."""
        tickets = [ticket for ticket in self.desk.tickets if ticket["status"] == "open"]
        if not tickets:
            return "Could you tell me a little more about what you need?"
        listed = "; ".join(
            f"{ticket['ticket']}, {ticket['summary']}" for ticket in tickets
        )
        return f"Which of your tickets is it about, and when would suit you? {listed}."

    def perform(self, action: str, arguments: dict[str, str]) -> str:
        """Does what the caller said yes to, and says what it did."""
        raise NotImplementedError
