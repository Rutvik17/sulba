"""A zone's trips hour by hour through a day."""

from datetime import date, datetime, time, timedelta

import psycopg

HOURLY = """
WITH counts AS (
    SELECT date_trunc('hour', pickup_at) AS hour, count(*) AS trips
    FROM trips
    WHERE pickup_zone = %(zone)s AND pickup_at >= %(start)s AND pickup_at < %(end)s
    GROUP BY 1
), series AS (
    SELECT h.hour, coalesce(c.trips, 0) AS trips
    FROM generate_series(%(start)s, %(end)s - interval '1 hour', interval '1 hour') AS h(hour)
    LEFT JOIN counts c ON c.hour = h.hour
)
SELECT hour, trips,
    (sum(trips) OVER (ORDER BY hour))::bigint AS running,
    (avg(trips) OVER (ORDER BY hour ROWS BETWEEN 2 PRECEDING AND CURRENT ROW))::float8
        AS rolling,
    trips - lag(trips) OVER (ORDER BY hour) AS change
FROM series
ORDER BY hour
"""


def hourly(
    conn: psycopg.Connection, zone: int, day: date
) -> list[tuple[datetime, int, int, float, int | None]]:
    """Each hour of day: the trips picked up in zone, the day's trips so far, the mean
    of this hour's and the two before it, and the change from the hour before."""
    start = datetime.combine(day, time())
    end = start + timedelta(days=1)
    return conn.execute(HOURLY, {"zone": zone, "start": start, "end": end}).fetchall()
