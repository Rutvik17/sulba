"""Books repairs from the shop's emails, or says why it can't."""

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

import httpx

from extract import NoMatch, ask_for

INSTRUCTIONS = (
    "You read the emails a bicycle repair shop gets. When an email asks to book a repair, "
    "fill in the booking from it, and otherwise set booking to null. Today is {today}."
)
BIKES = ["road", "mountain", "city", "cargo", "e-bike"]
SERVICES = ["puncture", "brakes", "gears", "full service"]
# The times a booking can start, on the hour and the half hour: Monday to Friday, and Saturday.
TIMES = [f"{hour:02}:{minute:02}" for hour in range(9, 17) for minute in (0, 30)]
SATURDAY = TIMES[: TIMES.index("12:30") + 1]
# How far ahead the shop takes bookings.
AHEAD = timedelta(days=28)


@dataclass(frozen=True)
class Booking:
    """A booking in the shop's calendar."""

    name: str
    bike: str
    service: str
    day: date
    time: str
    bikes: int
    phone: str | None
    notes: str


class NotBooked(Exception):
    """An email the shop can't book as it stands, with why, for whoever answers it."""


FIELDS: dict[str, Any] = {
    "name": {"type": "string", "minLength": 1, "maxLength": 60},
    "bike": {"enum": BIKES},
    "service": {"enum": SERVICES},
    "date": {"type": "string", "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"},
    "time": {"enum": TIMES},
    "bikes": {"type": "integer", "minimum": 1, "maximum": 3},
    "phone": {"type": ["string", "null"], "pattern": "^\\+?[0-9 ]{7,15}$"},
    "notes": {"type": "string", "maxLength": 500},
}
FORM = {
    "type": "object",
    "properties": {
        "booking": {
            "type": ["object", "null"],
            "properties": FIELDS,
            "required": list(FIELDS),
            "additionalProperties": False,
        }
    },
    "required": ["booking"],
    "additionalProperties": False,
}


def book(client: httpx.Client, email: str, today: date) -> Booking:
    """The booking an email asks for. Raises NotBooked when it asks for none, or for one the
    shop can't take, and ModelError when the model's API answers with an error."""
    messages = [
        {"role": "system", "content": INSTRUCTIONS.format(today=today.isoformat())},
        {"role": "user", "content": email},
    ]
    try:
        reply = ask_for(client, messages, FORM, "booking")
    except NoMatch as error:
        raise NotBooked("The model's replies never fit the form.") from error
    found = reply["booking"]
    if found is None:
        raise NotBooked("The email doesn't ask to book a repair.")
    try:
        day = date.fromisoformat(found["date"])
    except ValueError as error:
        raise NotBooked(f"There's no date {found['date']}.") from error
    if not today < day <= today + AHEAD:
        raise NotBooked(f"The shop books from tomorrow to {today + AHEAD}, not {day}.")
    if day.weekday() == 6:
        raise NotBooked("The shop is closed on Sundays.")
    if day.weekday() == 5 and found["time"] not in SATURDAY:
        raise NotBooked(f"The shop's last booking on Saturdays is at {SATURDAY[-1]}.")
    return Booking(
        name=found["name"],
        bike=found["bike"],
        service=found["service"],
        day=day,
        time=found["time"],
        bikes=int(found["bikes"]),
        phone=found["phone"],
        notes=found["notes"],
    )
