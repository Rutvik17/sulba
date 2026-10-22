"""Each borough's busiest pickup zones on a day."""

from datetime import date, timedelta

import psycopg

BUSIEST = """
WITH counts AS (
    SELECT z.borough, z.zone, z.name, count(*) AS trips,
        percentile_cont(0.5) WITHIN GROUP (ORDER BY t.fare) AS median_fare
    FROM trips t
    JOIN zones z ON z.zone = t.pickup_zone
    WHERE t.pickup_at >= %(start)s AND t.pickup_at < %(end)s
        AND z.borough IS NOT NULL
    GROUP BY z.borough, z.zone, z.name
), ranked AS (
    SELECT borough, zone, name, trips,
        trips::float8 / sum(trips) OVER (PARTITION BY borough) AS share,
        median_fare,
        rank() OVER (PARTITION BY borough ORDER BY trips DESC) AS rank
    FROM counts
)
SELECT borough, zone, name, trips, share, median_fare, rank
FROM ranked
WHERE rank <= %(n)s
ORDER BY borough, rank, zone
"""


def busiest(
    conn: psycopg.Connection, day: date, n: int = 3
) -> list[tuple[str, int, str, int, float, float, int]]:
    """Each borough's zones ranked n or better by the trips picked up there on day, with
    their share of the borough's trips, their median fare and their rank."""
    start = day
    end = day + timedelta(days=1)
    return conn.execute(BUSIEST, {"start": start, "end": end, "n": n}).fetchall()
