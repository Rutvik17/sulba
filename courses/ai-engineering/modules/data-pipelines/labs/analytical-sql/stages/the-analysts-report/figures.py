from datetime import date, datetime, time, timedelta

import pandas as pd

DAY = date(2025, 8, 5)


def figures():
    start = datetime.combine(DAY, time())
    end = start + timedelta(days=1)
    trips = pd.read_parquet(
        "data/yellow_tripdata_2025-08.parquet",
        columns=["tpep_pickup_datetime", "PULocationID", "passenger_count"],
        filters=[
            ("tpep_pickup_datetime", ">=", start),
            ("tpep_pickup_datetime", "<=", end),
        ],
    )
    zones = pd.read_csv("data/taxi_zone_lookup.csv", keep_default_na=False)
    borough = dict(zip(zones["LocationID"], zones["Borough"], strict=True))
    day = trips[trips["tpep_pickup_datetime"] < end]
    boroughs = day["PULocationID"].map(borough)
    manhattan = day.loc[boroughs == "Manhattan", "passenger_count"]
    return {
        "unknown": f"{boroughs.isin(['N/A', 'Unknown']).sum():,}",
        "unreported": f"{day['passenger_count'].isna().sum():,}",
        "manhattan": f"{len(manhattan):,}",
        "manhattan_counted": f"{manhattan.notna().sum():,}",
        "per_trip": f"{manhattan.mean():.2f}",
        "per_trip_zeros": f"{manhattan.fillna(0).mean():.2f}",
        "midnight": str((trips["tpep_pickup_datetime"] == end).sum()),
    }
