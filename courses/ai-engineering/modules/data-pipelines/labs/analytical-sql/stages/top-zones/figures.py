from datetime import date, datetime, time, timedelta

import pandas as pd

DAY = date(2025, 8, 5)


def figures():
    start = datetime.combine(DAY, time())
    end = start + timedelta(days=1)
    trips = pd.read_parquet(
        "data/yellow_tripdata_2025-08.parquet",
        columns=["tpep_pickup_datetime", "PULocationID"],
        filters=[
            ("tpep_pickup_datetime", ">=", start),
            ("tpep_pickup_datetime", "<=", end),
        ],
    )
    zones = pd.read_csv("data/taxi_zone_lookup.csv", keep_default_na=False)
    unknown = zones.loc[zones["Borough"].isin(["N/A", "Unknown"]), "LocationID"]
    day = trips[trips["tpep_pickup_datetime"] < end]
    return {
        "zones": f"{len(zones):,}",
        "trips": f"{len(day):,}",
        "unknown": f"{day['PULocationID'].isin(unknown).sum():,}",
        "midnight": str((trips["tpep_pickup_datetime"] == end).sum()),
    }
