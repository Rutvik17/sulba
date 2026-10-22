from datetime import date, datetime, time, timedelta

import pandas as pd

DAY = date(2025, 8, 5)
# Williamsburg (North Side) and Midtown Center.
QUIET = 255
BUSY = 161


def figures():
    start = datetime.combine(DAY, time())
    trips = pd.read_parquet(
        "data/yellow_tripdata_2025-08.parquet",
        columns=["tpep_pickup_datetime", "PULocationID"],
        filters=[
            ("tpep_pickup_datetime", ">=", start),
            ("tpep_pickup_datetime", "<", start + timedelta(days=1)),
        ],
    )
    hours = trips["tpep_pickup_datetime"].dt.hour

    def counts(zone):
        return (
            hours[trips["PULocationID"] == zone]
            .value_counts()
            .reindex(range(24), fill_value=0)
        )

    quiet = counts(QUIET)
    busy = counts(BUSY)
    return {
        "empty": str((quiet == 0).sum()),
        "quiet_trips": str(quiet.sum()),
        "busy_trips": f"{busy.sum():,}",
        "busy_peak": str(busy.max()),
        "busy_peak_hour": f"{busy.idxmax():02d}:00",
    }
