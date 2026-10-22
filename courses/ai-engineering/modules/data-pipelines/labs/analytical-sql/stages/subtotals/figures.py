from datetime import date, datetime, time, timedelta
from decimal import ROUND_HALF_UP, Decimal

import pandas as pd

DAY = date(2025, 8, 5)
CENT = Decimal("0.01")


def figures():
    start = datetime.combine(DAY, time())
    trips = pd.read_parquet(
        "data/yellow_tripdata_2025-08.parquet",
        columns=["tpep_pickup_datetime", "payment_type", "total_amount"],
        filters=[
            ("tpep_pickup_datetime", ">=", start),
            ("tpep_pickup_datetime", "<", start + timedelta(days=1)),
        ],
    )
    takings = sum(
        Decimal(repr(amount)).quantize(CENT, ROUND_HALF_UP)
        for amount in trips["total_amount"]
    )
    return {
        "trips": f"{len(trips):,}",
        "takings": f"{takings:,}",
        "flex": f"{(trips['payment_type'] == 0).sum():,}",
        "payments": str(trips["payment_type"].nunique()),
    }
