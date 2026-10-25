import csv
from datetime import date, datetime, timedelta

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

FILES = [
    ("data/yellow_tripdata_2025-08.parquet", "tpep"),
    ("data/green_tripdata_2025-08.parquet", "lpep"),
]
# The assistant's names, which it looked up by Spark's day of the week, 1 for a Sunday.
WEEKDAYS = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]


def clean_trips():
    """The clean trips, how many of them report no passengers, and each borough and day with
    one."""
    with open("data/taxi_zone_lookup.csv", encoding="utf-8", newline="") as file:
        borough = {
            int(row["LocationID"]): row["Borough"] for row in csv.DictReader(file)
        }
    clean, unreported, found = 0, 0, set()
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
        kept = table.filter(pc.invert(flag))
        clean += kept.num_rows
        unreported += kept["passenger_count"].null_count
        days = pc.cast(kept[f"{prefix}_pickup_datetime"], pa.date32()).to_pylist()
        for zone, day in zip(kept["PULocationID"].to_pylist(), days):
            found.add((day, borough[zone]))
    return clean, unreported, found


def figures():
    with open("data/central-park-2025-08.csv", encoding="utf-8", newline="") as file:
        traces = [
            date.fromisoformat(row["DATE"])
            for row in csv.DictReader(file)
            if row["PRCP_ATTRIBUTES"].split(",")[0] == "T"
        ]
    clean, unreported, found = clean_trips()
    first = date(2025, 8, 1)
    days = [first + timedelta(days=n) for n in range(31)]
    (empty,) = [day for day in days if (day, "Staten Island") not in found]
    sunday_first = first.isoweekday() % 7 + 1
    return {
        "traces": " and ".join(f"{day.day}" for day in traces) + " August",
        "clean": f"{clean:,}",
        "unreported": f"{unreported:,}",
        "first_weekday": first.strftime("%A"),
        "first_named": WEEKDAYS[sunday_first - 1],
        "empty_day": f"{empty.day} August",
    }
