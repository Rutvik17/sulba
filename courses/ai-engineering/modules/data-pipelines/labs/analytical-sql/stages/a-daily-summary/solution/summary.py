"""Each day's trips by zone, kept in a table the dashboards read."""

from datetime import date, timedelta

import psycopg

CREATE = """
CREATE TABLE IF NOT EXISTS daily_zones (
    day date NOT NULL,
    zone integer NOT NULL,
    pickups integer NOT NULL,
    dropoffs integer NOT NULL,
    revenue numeric(12, 2) NOT NULL,
    PRIMARY KEY (day, zone)
)
"""

WRITE = """
WITH day_trips AS (
    SELECT pickup_zone, dropoff_zone, total
    FROM trips
    WHERE pickup_at >= %(start)s AND pickup_at < %(end)s
), pickups AS (
    SELECT pickup_zone AS zone, count(*) AS pickups, sum(total) AS revenue
    FROM day_trips
    GROUP BY pickup_zone
), dropoffs AS (
    SELECT dropoff_zone AS zone, count(*) AS dropoffs
    FROM day_trips
    GROUP BY dropoff_zone
)
INSERT INTO daily_zones (day, zone, pickups, dropoffs, revenue)
SELECT %(start)s, coalesce(p.zone, d.zone), coalesce(p.pickups, 0),
    coalesce(d.dropoffs, 0), coalesce(p.revenue, 0)
FROM pickups p
FULL JOIN dropoffs d ON d.zone = p.zone
"""


def refresh(conn: psycopg.Connection, day: date) -> int:
    """Replaces day's rows in daily_zones, all of them or none, with each zone's pickups,
    drop-offs and takings that day, and returns how many zones it wrote."""
    with conn.transaction():
        conn.execute(CREATE)
        conn.execute("DELETE FROM daily_zones WHERE day = %s", (day,))
        written = conn.execute(WRITE, {"start": day, "end": day + timedelta(days=1)})
        return written.rowcount
