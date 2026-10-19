"""The shop's assistant: it answers a signed-in customer with the shop's tools, proposes
cancellations for them to confirm, and keeps each customer to a day's tokens."""

import json
import sqlite3
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import httpx

from actions import Actions, Pending, Refused
from render import render
from shop import TOOLS, Tools, tool

MODEL = "Qwen3.5-0.8B"
INSTRUCTIONS = (
    "You answer customers of a bicycle repair shop, in a sentence or two. Use the tools "
    "for their bookings, the times already booked on a day, and reviews of parts. "
    "Members get 10% off a full service with the code SPOKES10."
)
SORRY = "Sorry, I can't answer that right now. Please call the shop."
SPENT = "You've reached today's limit. Please call the shop."
ROUNDS = 4
REPLY_TOKENS = 400
# The tokens a customer's conversations can take in a day.
DAILY_TOKENS = 20_000
TAKEN = tool(
    "taken_times", "The times already booked on a day, as YYYY-MM-DD.", ["day"]
)
CANCEL = tool(
    "cancel_booking",
    "Asks the customer to confirm cancelling one of their bookings.",
    ["reference"],
)
CONFIRM = tool(
    "confirm_cancel", "Cancels a booking once the customer has said yes.", ["id"]
)


@dataclass
class Reply:
    """What the chat window shows: the reply as HTML, and a button for each action."""

    html: str
    actions: list[Pending]


class Assistant:
    """Answers one signed-in customer."""

    def __init__(
        self,
        client: httpx.Client,
        db: sqlite3.Connection,
        actions: Actions,
        customer: str,
        clock: Callable[[], datetime],
    ) -> None:
        self.client = client
        self.db = db
        self.actions = actions
        self.customer = customer
        self.clock = clock
        self.tools = Tools(db, customer)
        self.offered = [*TOOLS, TAKEN, CANCEL, CONFIRM]
        db.execute(
            "CREATE TABLE IF NOT EXISTS usage"
            " (customer TEXT, day TEXT, tokens INTEGER, PRIMARY KEY (customer, day))"
        )

    def answer(self, question: str) -> Reply:
        """The reply to the customer's question."""
        if self.used() >= DAILY_TOKENS:
            return Reply(render(SPENT), [])
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": INSTRUCTIONS},
            {"role": "user", "content": question},
        ]
        pending: list[Pending] = []
        for _ in range(ROUNDS):
            body = {
                "model": MODEL,
                "messages": messages,
                "tools": self.offered,
                "max_completion_tokens": REPLY_TOKENS,
            }
            response = self.client.post("/chat/completions", json=body)
            if response.is_error:
                return Reply(render(SORRY), pending)
            reply = response.json()
            self.spend(reply["usage"]["completion_tokens"])
            choice = reply["choices"][0]
            if choice["finish_reason"] == "stop":
                return Reply(render(choice["message"]["content"] or SORRY), pending)
            if choice["finish_reason"] != "tool_calls":
                return Reply(render(SORRY), pending)
            messages.append(choice["message"])
            for call in choice["message"]["tool_calls"]:
                content = self.run(call, pending)
                messages.append(
                    {"role": "tool", "tool_call_id": call["id"], "content": content}
                )
        return Reply(render(SORRY), pending)

    def run(self, call: dict[str, Any], pending: list[Pending]) -> str:
        """The content of the tool message that answers a call."""
        name = call["function"]["name"]
        try:
            arguments = json.loads(call["function"]["arguments"])
            if name == "taken_times":
                rows = self.db.execute(
                    "SELECT * FROM bookings WHERE day = ? AND status = 'booked'"
                    " ORDER BY time",
                    (arguments["day"],),
                )
                return json.dumps({"taken": [list(row) for row in rows]})
            if name == "cancel_booking":
                action = self.actions.propose_cancel(
                    self.customer, arguments["reference"], self.clock()
                )
                pending.append(action)
                return json.dumps(
                    {"waiting_for_the_customer": action.question, "id": action.id}
                )
            if name == "confirm_cancel":
                done = self.actions.confirm(
                    self.customer, arguments["id"], self.clock()
                )
                return json.dumps({"done": done})
        except (Refused, ValueError, KeyError, TypeError, sqlite3.Error) as error:
            return json.dumps({"error": str(error)})
        return self.tools.run(call)

    def confirm(self, id: str) -> Reply:
        """The reply when the customer presses an action's confirm button."""
        try:
            return Reply(
                render(self.actions.confirm(self.customer, id, self.clock())), []
            )
        except Refused as refused:
            return Reply(render(str(refused)), [])

    def used(self) -> int:
        """The tokens the customer's conversations have taken today."""
        row = self.db.execute(
            "SELECT tokens FROM usage WHERE customer = ? AND day = ?",
            (self.customer, self.clock().date().isoformat()),
        ).fetchone()
        return row[0] if row else 0

    def spend(self, tokens: int) -> None:
        """Adds a request's tokens to the customer's day."""
        self.db.execute(
            "INSERT INTO usage VALUES (?, ?, ?) ON CONFLICT (customer, day)"
            " DO UPDATE SET tokens = tokens + excluded.tokens",
            (self.customer, self.clock().date().isoformat(), tokens),
        )
