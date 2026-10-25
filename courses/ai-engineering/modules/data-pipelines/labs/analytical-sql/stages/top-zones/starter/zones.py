"""Each borough's busiest pickup zones on a day."""

from datetime import date

import psycopg


def busiest(
    conn: psycopg.Connection, day: date, n: int = 3
) -> list[tuple[str, int, str, int, float, float, int]]:
    """Each borough's zones ranked n or better by the trips picked up there on day, with
    their share of the borough's trips, their median fare and their rank."""
    raise NotImplementedError
