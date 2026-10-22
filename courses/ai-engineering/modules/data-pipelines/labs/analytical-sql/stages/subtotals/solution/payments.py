"""A day's trips and takings by borough and payment, with subtotals."""

from datetime import date, timedelta
from decimal import Decimal

import psycopg

BY_PAYMENT = """
SELECT
    CASE GROUPING(z.borough, p.payment)
        WHEN 0 THEN 'payment'
        WHEN 1 THEN 'borough'
        ELSE 'all'
    END AS level,
    z.borough, p.name, count(*) AS trips, sum(t.total) AS revenue
FROM trips t
JOIN zones z ON z.zone = t.pickup_zone
JOIN payments p ON p.payment = t.payment
WHERE t.pickup_at >= %(start)s AND t.pickup_at < %(end)s
GROUP BY ROLLUP (z.borough, (p.payment, p.name))
ORDER BY GROUPING(z.borough), z.borough NULLS LAST, GROUPING(p.payment), p.payment
"""


def by_payment(
    conn: psycopg.Connection, day: date
) -> list[tuple[str, str | None, str | None, int, Decimal]]:
    """The trips picked up on day and what riders paid for them, by pickup borough and
    payment, with each borough's subtotal and the day's total."""
    start = day
    end = day + timedelta(days=1)
    return conn.execute(BY_PAYMENT, {"start": start, "end": end}).fetchall()
