"""Actions with side effects, which wait for the customer to confirm them."""

import secrets
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta

# How long a customer has to confirm an action.
WAIT = timedelta(minutes=10)


@dataclass(frozen=True)
class Pending:
    """An action waiting for its customer: the question their confirm button asks, and the id
    the chat window sends back when they press it."""

    id: str
    customer: str
    reference: str
    question: str
    expires: datetime


class Refused(Exception):
    """An action that can't be taken, with the reason, for the customer to read."""


class Actions:
    """Proposes actions for customers, and takes each one when its customer confirms it."""

    def __init__(self, db: sqlite3.Connection) -> None:
        self.db = db
        self.pending: dict[str, Pending] = {}

    def propose_cancel(self, customer: str, reference: str, now: datetime) -> Pending:
        """An action that cancels one of the customer's bookings once they confirm it."""
        row = self.db.execute(
            "SELECT service, day, time FROM bookings"
            " WHERE reference = ? AND customer = ? AND status = 'booked'",
            (reference, customer),
        ).fetchone()
        if row is None:
            raise Refused(f"There's no booking {reference} to cancel.")
        service, day, time = row
        question = f"Cancel booking {reference}, {service} on {day} at {time}?"
        action = Pending(
            secrets.token_urlsafe(16), customer, reference, question, now + WAIT
        )
        self.pending[action.id] = action
        return action

    def confirm(self, customer: str, id: str, now: datetime) -> str:
        """Takes the action whose button the customer pressed, once, before it expires."""
        action = self.pending.get(id)
        if action is None or action.customer != customer:
            raise Refused("That action isn't waiting for you.")
        del self.pending[id]
        if now >= action.expires:
            raise Refused("That action has expired.")
        cancelled = self.db.execute(
            "UPDATE bookings SET status = 'cancelled'"
            " WHERE reference = ? AND customer = ? AND status = 'booked'",
            (action.reference, customer),
        ).rowcount
        if not cancelled:
            raise Refused(f"Booking {action.reference} can't be cancelled now.")
        return f"Booking {action.reference} is cancelled."
