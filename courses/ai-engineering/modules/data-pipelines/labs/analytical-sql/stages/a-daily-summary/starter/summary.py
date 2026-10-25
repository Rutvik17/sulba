"""Each day's trips by zone, kept in a table the dashboards read."""

from datetime import date

import psycopg


def refresh(conn: psycopg.Connection, day: date) -> int:
    """Replaces day's rows in daily_zones, all of them or none, with each zone's pickups,
    drop-offs and takings that day, and returns how many zones it wrote."""
    raise NotImplementedError
