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
    opened = f" They opened the chat on the {SERVICES[page]} pages." if page else ""
    try:
        found = json.loads(
            chat(
                client,
                [
                    {"role": "system", "content": ROUTER + opened},
                    {"role": "user", "content": message},
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {"schema": ROUTE},
                },
            )
        )
        values = {
            key: None if found[key] == "none" else found[key]
            for key in ROUTE["required"]
        }
    except json.JSONDecodeError, KeyError, TypeError:
        return Route("other")
    if values["kind"] not in ("question", "case", "callback"):
        return Route("other")
    return Route(
        values["kind"],
        values["service"] or page,
        WEEKDAYS.get(values["day"] or ""),
        values["time"],
        values["part"],
    )


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
        self.desk.turn = self.turns
        self.turns += 1
        pending, self.pending = self.pending, None
        if pending is not None and YES.match(message):
            return self.perform(*pending)
        return self.follow(message, found or route(self.client, message, self.page))

    def follow(self, message: str, found: Route) -> str:
        """The reply down the path of the message's route."""
        if found.kind == "question":
            return self.answer(message, found.service)
        if found.kind == "case" and found.service:
            self.pending = ("open", {"service": found.service, "summary": message})
            return (
                f"I can open a ticket for a {SERVICES[found.service]} adviser to look into "
                "this. Shall I?"
            )
        if found.kind == "callback" and found.service and found.day:
            return self.callback(message, found)
        return self.ask()

    def answer(self, question: str, service: str | None) -> str:
        """The answer to a question, from the passages the search finds for it."""
        found = self.desk.search.find(question, service)
        shown = "\n\n".join(
            f"[{each['passage']}] {each['page']}\n{each['text']}" for each in found
        )
        return chat(
            self.client,
            [
                {"role": "system", "content": ANSWER},
                {
                    "role": "user",
                    "content": f"Passages:\n\n{shown}\n\nQuestion: {question}",
                },
            ],
        )

    def callback(self, message: str, found: Route) -> str:
        """The offer of a callback the route asks for, or a question when the desk can't place it."""
        assert found.service and found.day
        tickets = [
            ticket
            for ticket in self.desk.tickets
            if ticket["service"] == found.service and ticket["status"] == "open"
        ]
        if len(tickets) > 1:
            return self.ask()
        free = self.desk.free[found.service][found.day]
        times = [
            time
            for time in free
            if (found.time is None or time == found.time)
            and (found.part is None or (time < "12:00") == (found.part == "morning"))
        ]
        if not times:
            return (
                f"The {SERVICES[found.service]} advisers aren't free then on "
                f"{DAYS[found.day]}. They're free at {', '.join(free)}. Which suits you?"
            )
        when = {"day": found.day, "time": times[0]}
        if tickets:
            ticket = tickets[0]["ticket"]
            self.pending = ("book", {"ticket": ticket, **when})
            about = f"ticket {ticket}, {tickets[0]['summary']}"
        else:
            self.pending = (
                "open and book",
                {"service": found.service, "summary": message, **when},
            )
            about = f"a new ticket for {SERVICES[found.service]}"
        return (
            f"I can book an adviser to call you on {DAYS[found.day]} {found.day} at {times[0]} "
            f"about {about}. Shall I?"
        )

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
        if action == "open":
            ticket = self.desk.open_ticket(arguments["service"], arguments["summary"])[
                "ticket"
            ]
            return f"I've opened ticket {ticket}. An adviser will look into it."
        if action == "open and book":
            opened = self.desk.open_ticket(arguments["service"], arguments["summary"])
            arguments = {
                "ticket": opened["ticket"],
                "day": arguments["day"],
                "time": arguments["time"],
            }
        booked = self.desk.book_callback(**arguments)
        if "error" in booked:
            return f"I couldn't book that: {booked['error']}"
        day, time = arguments["day"], arguments["time"]
        return (
            f"Booked: an adviser will call you on {DAYS[day]} {day} at {time} about ticket "
            f"{arguments['ticket']}."
        )
