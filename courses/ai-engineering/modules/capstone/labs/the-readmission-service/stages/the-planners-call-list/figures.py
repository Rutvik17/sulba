import pandas as pd

DEATH_OR_HOSPICE = [11, 13, 14, 19, 20, 21]
BATCH = 100
# The day of discharges the second check sends.
DAY = 250


def figures():
    encounters = pd.read_csv(
        "data/encounters.csv", na_values=["?"], keep_default_na=False
    )
    untested = (encounters["A1Cresult"] == "None").mean()
    ended = encounters["discharge_disposition_id"].isin(DEATH_OR_HOSPICE).mean()
    # The stays a batch one short never sent: the last of each full batch.
    missing = len(range(BATCH - 1, DAY, BATCH))
    return {
        "none_share": f"{untested:.0%}",
        "ended_share": f"{ended:.1%}",
        "batch_refused": f"{1 - (1 - ended) ** BATCH:.0%}",
        "day": str(DAY),
        "missing": str(missing),
    }
