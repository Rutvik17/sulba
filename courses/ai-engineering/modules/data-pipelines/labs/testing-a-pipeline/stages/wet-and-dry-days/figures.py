import csv
from datetime import date, datetime, timedelta
from statistics import fmean

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

FILES = [
    ("data/yellow_tripdata_2025-08.parquet", "tpep"),
    ("data/green_tripdata_2025-08.parquet", "lpep"),
]
DAYS = [date(2025, 8, 1) + timedelta(days=n) for n in range(31)]


def counts():
    """Each borough's clean pickups on each day, as {(day, borough): trips}."""
    with open("data/taxi_zone_lookup.csv", encoding="utf-8", newline="") as file:
        borough = {
            int(row["LocationID"]): row["Borough"] for row in csv.DictReader(file)
        }
    result = {}
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
        flag = pc.fill_null(flags[0], False)
        for other in flags[1:]:
            flag = pc.or_(flag, pc.fill_null(other, False))
        clean = table.filter(pc.invert(flag))
        days = pc.cast(clean[f"{prefix}_pickup_datetime"], pa.date32()).to_pylist()
        for zone, day in zip(clean["PULocationID"].to_pylist(), days):
            key = (day, borough[zone])
            result[key] = result.get(key, 0) + 1
    return result


def figures():
    with open("data/central-park-2025-08.csv", encoding="utf-8", newline="") as file:
        wet = {
            date.fromisoformat(row["DATE"]): int(row["PRCP"]) / 10 >= 1
            for row in csv.DictReader(file)
        }
    trips = counts()

    def mean(borough, days):
        return fmean(trips.get((day, borough), 0) for day in days)

    def dry_like(day):
        return [
            other
            for other in DAYS
            if other.weekday() == day.weekday() and not wet[other]
        ]

    def change(borough, day):
        return trips.get((day, borough), 0) / mean(borough, dry_like(day)) - 1

    wet_days = [day for day in DAYS if wet[day]]
    dry_days = [day for day in DAYS if not wet[day]]
    wednesdays = [day for day in wet_days if day.weekday() == 2]
    (dry_wednesday,) = dry_like(wednesdays[0])
    biggest = max(wednesdays, key=lambda day: change("Manhattan", day))
    thursday = next(day for day in wet_days if day.weekday() == 3)
    return {
        "wet_days": str(len(wet_days)),
        "wet_wednesdays": str(len(wednesdays)),
        "dry_wednesday": f"{dry_wednesday.day} August",
        "manhattan_wet": f"{mean('Manhattan', wet_days):,.0f}",
        "manhattan_dry": f"{mean('Manhattan', dry_days):,.0f}",
        "queens_wet": f"{mean('Queens', wet_days):,.0f}",
        "queens_dry": f"{mean('Queens', dry_days):,.0f}",
        "manhattan_wednesday": f"{biggest.day} August",
        "manhattan_wednesday_trips": f"{trips[biggest, 'Manhattan']:,}",
        "manhattan_dry_wednesday_trips": f"{trips[dry_wednesday, 'Manhattan']:,}",
        "manhattan_wednesday_change": f"{change('Manhattan', biggest):.1%}",
        "thursday": f"{thursday.day} August",
        "dry_thursdays": str(len(dry_like(thursday))),
        "manhattan_thursday_change": f"{-change('Manhattan', thursday):.1%}",
        "ewr_wednesday_trips": str(trips[biggest, "EWR"]),
        "ewr_dry_wednesday_trips": str(trips[dry_wednesday, "EWR"]),
        "ewr_wednesday_change": f"{change('EWR', biggest):.0%}",
    }
