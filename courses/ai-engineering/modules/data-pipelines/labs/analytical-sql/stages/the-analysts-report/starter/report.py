"""The morning report: the day's trips by pickup borough."""

from datetime import date, timedelta

import psycopg

REPORT = """
WITH counts AS (
    SELECT z.borough,
        count(t.passengers) AS trips,
        avg(coalesce(t.passengers, 0)) AS passengers
    FROM trips t
    JOIN zones z ON z.zone = t.pickup_zone
    WHERE t.pickup_at BETWEEN %(start)s AND %(end)s
        AND z.borough <> 'EWR'
    GROUP BY z.borough
)
SELECT borough, trips, passengers::float8, trips::float8 / sum(trips) OVER () AS share
FROM counts
ORDER BY borough NULLS LAST
"""


def boroughs(
    conn: psycopg.Connection, day: date
) -> list[tuple[str | None, int, float, float]]:
    """Each pickup borough's trips on day, its passengers per trip and its share of the
    day's trips, Newark's left out."""
    start = day
    end = day + timedelta(days=1)
    return conn.execute(REPORT, {"start": start, "end": end}).fetchall()
