"""Actions with side effects, which wait for the customer to confirm them."""

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
        raise NotImplementedError

    def confirm(self, customer: str, id: str, now: datetime) -> str:
        """Takes the action whose button the customer pressed, once, before it expires."""
        raise NotImplementedError
