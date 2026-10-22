from datetime import date, datetime, time, timedelta

import pandas as pd

DAY = date(2025, 8, 5)


def figures():
    start = datetime.combine(DAY, time())
    trips = pd.read_parquet(
        "data/yellow_tripdata_2025-08.parquet",
        columns=["tpep_pickup_datetime", "PULocationID", "DOLocationID"],
        filters=[
            ("tpep_pickup_datetime", ">=", start),
            ("tpep_pickup_datetime", "<", start + timedelta(days=1)),
        ],
    )
    pickups = set(trips["PULocationID"])
    dropoffs = set(trips["DOLocationID"])
    return {
        "zones": str(len(pickups | dropoffs)),
        "dropoffs_only": str(len(dropoffs - pickups)),
    }
