"""The shop's tools for its assistant, each answering only for the customer who's signed in."""

import json
import sqlite3
from typing import Any

# The shop's tables. A booking's notes are what the customer or the shop wrote about the repair.
SCHEMA = """
CREATE TABLE bookings (
    reference TEXT PRIMARY KEY, customer TEXT NOT NULL, day TEXT NOT NULL,
    time TEXT NOT NULL, service TEXT NOT NULL, bike TEXT NOT NULL, notes TEXT NOT NULL,
    status TEXT NOT NULL
);
CREATE TABLE reviews (
    id INTEGER PRIMARY KEY, part TEXT NOT NULL, author TEXT NOT NULL,
    stars INTEGER NOT NULL, text TEXT NOT NULL
);
"""


def tool(name: str, description: str, parameters: list[str]) -> dict[str, Any]:
    """A tool as the chat completions API takes it, its parameters all strings."""
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": {each: {"type": "string"} for each in parameters},
                "required": parameters,
                "additionalProperties": False,
            },
            "strict": True,
        },
    }


# The tools as the model sees them. None names a customer: they answer for the one signed in.
TOOLS = [
    tool("my_bookings", "The customer's bookings, soonest first.", []),
    tool("booking", "One of the customer's bookings, by its reference.", ["reference"]),
    tool("reviews", "What customers wrote about a part the shop sells.", ["part"]),
]
PARAMETERS = {
    each["function"]["name"]: each["function"]["parameters"]["required"]
    for each in TOOLS
}


class ToolError(Exception):
    """A call the tools won't answer, with the reason, for the model to read."""


class Tools:
    """The shop's tools, run for one signed-in customer."""

    def __init__(self, db: sqlite3.Connection, customer: str) -> None:
        self.db = db
        self.customer = customer

    def my_bookings(self) -> list[dict[str, Any]]:
        """The customer's bookings, soonest first."""
        rows = self.db.execute(
            "SELECT reference, day, time, service, status FROM bookings"
            " WHERE customer = ? ORDER BY day, time",
            (self.customer,),
        )
        keys = ("reference", "day", "time", "service", "status")
        return [dict(zip(keys, row)) for row in rows]

    def booking(self, reference: str) -> dict[str, Any]:
        """One of the customer's bookings. Another customer's reads as missing."""
        row = self.db.execute(
            "SELECT reference, day, time, service, bike, notes, status FROM bookings"
            " WHERE reference = ? AND customer = ?",
            (reference, self.customer),
        ).fetchone()
        if row is None:
            raise ToolError(f"There's no booking {reference}.")
        keys = ("reference", "day", "time", "service", "bike", "notes", "status")
        return dict(zip(keys, row))

    def reviews(self, part: str) -> list[dict[str, Any]]:
        """Each review of a part, oldest first: its stars and its text, not who wrote it."""
        rows = self.db.execute(
            "SELECT stars, text FROM reviews WHERE part = ? ORDER BY id", (part,)
        )
        return [{"stars": stars, "text": text} for stars, text in rows]

    def run(self, call: dict[str, Any]) -> str:
        """The content of the tool message that answers call: the tool's value as JSON, or an
        error the model can read. It never raises."""
        try:
            value = self.answer(call["function"]["name"], call["function"]["arguments"])
        except ToolError as error:
            value = {"error": str(error)}
        return json.dumps(value, ensure_ascii=False)

    def answer(self, name: str, arguments: str) -> Any:
        """The value of the tool name for its arguments, as JSON text."""
        if name not in PARAMETERS:
            raise ToolError(f"There's no tool called {name!r}.")
        try:
            values = json.loads(arguments)
        except json.JSONDecodeError as error:
            raise ToolError(f"The arguments aren't JSON: {error}") from None
        expected = PARAMETERS[name]
        if (
            not isinstance(values, dict)
            or sorted(values) != sorted(expected)
            or not all(isinstance(value, str) for value in values.values())
        ):
            raise ToolError(f"{name} takes {expected}, each a string.")
        return getattr(self, name)(**values)
