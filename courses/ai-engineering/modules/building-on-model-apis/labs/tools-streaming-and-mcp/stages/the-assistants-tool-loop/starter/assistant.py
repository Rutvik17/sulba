"""The shop's assistant: it answers a customer's question with the shop's tools."""

import json
from typing import Any, Literal

import httpx

from tools import describe

MODEL = "Qwen3.5-0.8B"
INSTRUCTIONS = (
    "You answer customers for a bicycle repair shop, in a sentence or two. "
    "Use the tools for the shop's hours, prices and bookings."
)
SORRY = "Sorry, I can't answer that right now. Please call the shop."
ROUNDS = 4
Day = Literal[
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"
]
Service = Literal["puncture", "brakes", "gears", "full service"]
# Each refund the shop has paid, with its booking and amount.
REFUNDS: list[tuple[str, float]] = []


def opening_hours(day: Day) -> str:
    """The shop's opening hours on a day of the week."""
    return {"Saturday": "9:00 to 13:00", "Sunday": "Closed"}.get(day, "9:00 to 17:00")


def repair_price(service: Service, bikes: int) -> float:
    """The price of a repair, in pounds."""
    if bikes < 1:
        raise ValueError("A repair is for one bike or more.")
    return {"puncture": 12.0, "brakes": 18.0, "gears": 25.0, "full service": 60.0}[
        service
    ] * bikes


def refund(booking: str, amount: float) -> str:
    """Pays a customer back for a booking. Only the shop's staff use it."""
    REFUNDS.append((booking, amount))
    return f"Refunded £{amount:.2f} for {booking}."


TOOLS = {function.__name__: function for function in [opening_hours, repair_price]}


class Assistant:
    """Answers customers' questions, calling the shop's tools as the model asks."""

    def __init__(self, client: httpx.Client) -> None:
        self.client = client
        self.tools = [describe(function) for function in TOOLS.values()]

    def answer(self, question: str) -> str:
        """The model's answer to the question, or SORRY when it gives none."""
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": INSTRUCTIONS},
            {"role": "user", "content": question},
        ]
        while True:
            body = {"model": MODEL, "messages": messages, "tools": self.tools}
            response = self.client.post("/chat/completions", json=body)
            if response.is_error:
                return SORRY
            choice = response.json()["choices"][0]
            message = choice["message"]
            if choice["finish_reason"] == "stop":
                return message["content"] or SORRY
            if choice["finish_reason"] != "tool_calls":
                return SORRY
            messages.append(message)
            call = message["tool_calls"][0]
            content = json.dumps(run(call), ensure_ascii=False)
            messages.append(
                {"role": "tool", "tool_call_id": call["id"], "content": content}
            )
        return SORRY


def run(call: dict[str, Any]) -> Any:
    """What a tool call returns, or the error that stopped it, for the model to read."""
    function = globals()[call["function"]["name"]]
    return function(**json.loads(call["function"]["arguments"]))
