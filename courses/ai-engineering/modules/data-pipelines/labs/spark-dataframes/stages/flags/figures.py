from datetime import datetime, timedelta

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

FILES = [
    ("data/yellow_tripdata_2025-08.parquet", "tpep"),
    ("data/green_tripdata_2025-08.parquet", "lpep"),
]
FLAGS = [
    "outside_month",
    "backwards",
    "too_long",
    "no_distance",
    "negative",
    "unknown_zone",
]


def figures():
    counts = dict.fromkeys(FLAGS, 0)
    trips = flagged = 0
    for path, prefix in FILES:
        table = pq.read_table(path)
        pickup = table[f"{prefix}_pickup_datetime"]
        dropoff = table[f"{prefix}_dropoff_datetime"]
        unknown = pa.array([264, 265])
        flags = {
            "outside_month": pc.or_(
                pc.less(pickup, datetime(2025, 8, 1)),
                pc.greater_equal(pickup, datetime(2025, 9, 1)),
            ),
            "backwards": pc.less(dropoff, pickup),
            "too_long": pc.greater(
                dropoff, pc.add(pickup, pa.scalar(timedelta(hours=24)))
            ),
            "no_distance": pc.less_equal(table["trip_distance"], 0),
            "negative": pc.or_(
                pc.less(table["fare_amount"], 0), pc.less(table["total_amount"], 0)
            ),
            "unknown_zone": pc.or_(
                pc.is_in(table["PULocationID"], unknown),
                pc.is_in(table["DOLocationID"], unknown),
            ),
        }
        flags = {name: pc.fill_null(flag, False) for name, flag in flags.items()}
        any_flag = flags[FLAGS[0]]
        for name in FLAGS:
            counts[name] += pc.sum(flags[name].cast(pa.int64())).as_py()
            any_flag = pc.or_(any_flag, flags[name])
        trips += table.num_rows
        flagged += pc.sum(any_flag.cast(pa.int64())).as_py()
    return {
        **{name: f"{count:,}" for name, count in counts.items()},
        "trips": f"{trips:,}",
        "flagged": f"{flagged:,}",
        "clean": f"{trips - flagged:,}",
    }
