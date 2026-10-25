import math
from datetime import datetime

import pyarrow.compute as pc
import pyarrow.parquet as pq

YELLOW = "data/yellow_tripdata_2025-08.parquet"
GREEN = "data/green_tripdata_2025-08.parquet"


def august(path, prefix):
    """The file's trips, and those of them picked up in August 2025."""
    table = pq.read_table(path)
    pickup = table[f"{prefix}_pickup_datetime"]
    inside = pc.and_(
        pc.greater_equal(pickup, datetime(2025, 8, 1)),
        pc.less(pickup, datetime(2025, 9, 1)),
    )
    return table, table.filter(inside)


def total(column):
    """The sum of the column's values, leaving out the missing ones, rounded once."""
    return math.fsum(value for value in column.to_pylist() if value is not None)


def figures():
    yellow_all, yellow = august(YELLOW, "tpep")
    green_all, green = august(GREEN, "lpep")
    charges = total(yellow["congestion_surcharge"]) + total(
        yellow["cbd_congestion_fee"]
    )
    row_by_row = total(
        pc.add(yellow["congestion_surcharge"], yellow["cbd_congestion_fee"])
    )
    outside = (
        yellow_all.num_rows - yellow.num_rows + green_all.num_rows - green.num_rows
    )
    return {
        "green_takings": f"${total(green['total_amount']):,.2f}",
        "green_payments": f"{total(green['payment_type']):,.0f}",
        "yellow_trips": f"{yellow.num_rows:,}",
        "yellow_cards": f"{pc.sum(pc.equal(yellow['payment_type'], 1).cast('int64')).as_py():,}",
        "no_surcharge": f"{yellow['congestion_surcharge'].null_count:,}",
        "charges": f"${charges:,.2f}",
        "charges_row_by_row": f"${row_by_row:,.2f}",
        "outside": str(outside),
    }
