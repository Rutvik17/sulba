import csv
from datetime import date, datetime, timedelta

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

FILES = [
    ("data/yellow_tripdata_2025-08.parquet", "tpep"),
    ("data/green_tripdata_2025-08.parquet", "lpep"),
]
# A zone with days without pickups, and a day on which its last seven rows span more than a week.
EXAMPLE = 46
DAY = date(2025, 8, 15)


def clean_counts():
    """Each zone's clean pickups on each day, as {(zone, day): trips}."""
    counts = {}
    for path, prefix in FILES:
        table = pq.read_table(path)
        pickup = table[f"{prefix}_pickup_datetime"]
        dropoff = table[f"{prefix}_dropoff_datetime"]
        unknown = pa.array([264, 265])
        flags = [
            pc.or_(
                pc.less(pickup, datetime(2025, 8, 1)),
                pc.greater_equal(pickup, datetime(2025, 9, 1)),
            ),
            pc.less(dropoff, pickup),
            pc.greater(dropoff, pc.add(pickup, pa.scalar(timedelta(hours=24)))),
            pc.less_equal(table["trip_distance"], 0),
            pc.or_(pc.less(table["fare_amount"], 0), pc.less(table["total_amount"], 0)),
            pc.or_(
                pc.is_in(table["PULocationID"], unknown),
                pc.is_in(table["DOLocationID"], unknown),
            ),
        ]
        flagged = pc.fill_null(flags[0], False)
        for flag in flags[1:]:
            flagged = pc.or_(flagged, pc.fill_null(flag, False))
        clean = table.filter(pc.invert(flagged))
        days = (
            pa.table(
                {
                    "zone": clean["PULocationID"],
                    "day": pc.cast(clean[f"{prefix}_pickup_datetime"], pa.date32()),
                }
            )
            .group_by(["zone", "day"])
            .aggregate([("zone", "count")])
        )
        for zone, day, trips in zip(
            *(days[name].to_pylist() for name in days.column_names)
        ):
            counts[zone, day] = counts.get((zone, day), 0) + trips
    return counts


def figures():
    with open("data/taxi_zone_lookup.csv", encoding="utf-8", newline="") as file:
        lookup = {int(row["LocationID"]): row["Zone"] for row in csv.DictReader(file)}
    counts = clean_counts()
    zones = {zone for zone, _ in counts}
    gaps = [zone for zone in zones if sum(1 for z, _ in counts if z == zone) < 31]
    days = sorted(day for zone, day in counts if zone == EXAMPLE)
    week = sum(
        counts.get((EXAMPLE, DAY - timedelta(days=back)), 0) for back in range(7)
    )
    rows = [day for day in days if day <= DAY][-7:]
    rows_trips = sum(counts[EXAMPLE, day] for day in rows)
    return {
        "zones": str(len(lookup)),
        "with_trips": str(len(zones)),
        "gaps": str(len(gaps)),
        "example": lookup[EXAMPLE],
        "example_days": str(len(days)),
        "example_week": str(week),
        "example_mean": f"{week / 7:.2f}",
        "example_rows_from": f"{rows[0].day} August",
        "example_rows_mean": f"{rows_trips / len(rows):.2f}",
    }
