"""A zone's trips hour by hour through a day."""

from datetime import date, datetime

import psycopg


def hourly(
    conn: psycopg.Connection, zone: int, day: date
) -> list[tuple[datetime, int, int, float, int | None]]:
    """Each hour of day: the trips picked up in zone, the day's trips so far, the mean
    of this hour's and the two before it, and the change from the hour before."""
    raise NotImplementedError
