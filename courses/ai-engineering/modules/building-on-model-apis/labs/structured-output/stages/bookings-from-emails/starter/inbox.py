"""Books repairs from the shop's emails, or says why it can't."""

from dataclasses import dataclass
from datetime import date, timedelta

import httpx

INSTRUCTIONS = (
    "You read the emails a bicycle repair shop gets. When an email asks to book a repair, "
    "fill in the booking from it, and otherwise set booking to null. Today is {today}."
)
BIKES = ["road", "mountain", "city", "cargo", "e-bike"]
SERVICES = ["puncture", "brakes", "gears", "full service"]
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


def book(client: httpx.Client, email: str, today: date) -> Booking:
    """The booking an email asks for. Raises NotBooked when it asks for none, or for one the
    shop can't take, and ModelError when the model's API answers with an error."""
    raise NotImplementedError
