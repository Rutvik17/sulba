"""Turns customers' emails into entries for the shop's calendar."""

from datetime import date
from typing import Any

import httpx

from extract import NoMatch, ask_for

INSTRUCTIONS = (
    "Fill in the bicycle repair shop's booking form from the customer's email. "
    "Today is {today}."
)
FORM = {
    "type": "object",
    "properties": {
        "name": {"type": "string", "minLength": 1, "maxLength": 60},
        "bike": {"enum": ["road", "mountain", "city", "cargo", "e-bike"]},
        "service": {"enum": ["puncture", "brakes", "gears", "full service"]},
        "date": {"type": "string", "format": "date"},
        "time": {"type": "string", "pattern": "(09|1[0-6]):[03]0"},
        "bikes": {"type": "integer", "minimum": 1, "maximum": 3},
        "phone": {"type": ["string", "null"], "pattern": "^\\+?[0-9 ]{7,15}$"},
        "notes": {"type": "string", "maxLength": 500},
    },
    "required": ["name", "bike", "service", "date", "time", "bikes", "phone", "notes"],
}


class NotBooked(Exception):
    """An email the shop can't book as it stands, with why, for whoever answers it."""


def book(client: httpx.Client, email: str, today: date) -> dict[str, Any]:
    """The calendar entry for the booking an email asks for, as the form's JSON. Raises
    NotBooked when the shop can't take it."""
    messages = [
        {"role": "system", "content": INSTRUCTIONS.format(today=today.isoformat())},
        {"role": "user", "content": email},
    ]
    try:
        entry: dict[str, Any] = ask_for(client, messages, FORM, "booking")
    except NoMatch as error:
        raise NotBooked("The model's replies didn't fit the form.") from error
    day = date.fromisoformat(entry["date"])
    if day < today:
        raise NotBooked(f"{day} has passed.")
    if day.weekday() == 7:
        raise NotBooked("The shop is closed on Sundays.")
    return entry
