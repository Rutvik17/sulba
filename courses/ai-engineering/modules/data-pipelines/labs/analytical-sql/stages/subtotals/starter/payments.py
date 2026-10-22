"""A day's trips and takings by borough and payment, with subtotals."""

from datetime import date
from decimal import Decimal

import psycopg


def by_payment(
    conn: psycopg.Connection, day: date
) -> list[tuple[str, str | None, str | None, int, Decimal]]:
    """The trips picked up on day and what riders paid for them, by pickup borough and
    payment, with each borough's subtotal and the day's total."""
    raise NotImplementedError
