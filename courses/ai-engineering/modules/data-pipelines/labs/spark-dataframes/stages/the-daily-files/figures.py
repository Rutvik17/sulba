from datetime import datetime, timedelta

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

FILES = [
    ("data/yellow_tripdata_2025-08.parquet", "tpep"),
    ("data/green_tripdata_2025-08.parquet", "lpep"),
]
START = datetime(2025, 8, 5)


def figures():
    trips = clean = 0
    for path, prefix in FILES:
        table = pq.read_table(path)
        pickup = table[f"{prefix}_pickup_datetime"]
        table = table.filter(
            pc.and_(
                pc.greater_equal(pickup, START),
                pc.less(pickup, START + timedelta(days=1)),
            )
        )
        pickup = table[f"{prefix}_pickup_datetime"]
        dropoff = table[f"{prefix}_dropoff_datetime"]
        unknown = pa.array([264, 265])
        flags = [
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
        trips += table.num_rows
        clean += table.num_rows - pc.sum(flagged.cast(pa.int64())).as_py()
    return {"fifth": f"{clean:,}", "fifth_all": f"{trips:,}"}
