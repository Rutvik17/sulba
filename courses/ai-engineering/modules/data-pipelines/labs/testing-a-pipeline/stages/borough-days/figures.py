import csv
from datetime import date, datetime, timedelta

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

FILES = [
    ("data/yellow_tripdata_2025-08.parquet", "tpep"),
    ("data/green_tripdata_2025-08.parquet", "lpep"),
]


def clean_days():
    """Each borough and day with a clean pickup."""
    with open("data/taxi_zone_lookup.csv", encoding="utf-8", newline="") as file:
        borough = {
            int(row["LocationID"]): row["Borough"] for row in csv.DictReader(file)
        }
    found = set()
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
            found.add((day, borough[zone]))
    return found, sorted(set(borough.values()) - {"N/A", "Unknown"})


def figures():
    found, boroughs = clean_days()
    days = [date(2025, 8, 1) + timedelta(days=n) for n in range(31)]
    (empty,) = [day for day in days if (day, "Staten Island") not in found]
    return {
        "boroughs": str(len(boroughs)),
        "rows": str(len(days) * len(boroughs)),
        "empty_day": f"{empty.day} August",
    }
