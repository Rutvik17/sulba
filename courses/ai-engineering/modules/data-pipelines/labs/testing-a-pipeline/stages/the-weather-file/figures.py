import csv


def figures():
    with open("data/central-park-2025-08.csv", encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))
    rain = [row for row in rows if int(row["PRCP"]) > 0]
    trace = [row for row in rows if row["PRCP_ATTRIBUTES"].split(",")[0] == "T"]
    # The brief says no value in the file failed a quality check.
    assert all(
        value.split(",")[1] == ""
        for row in rows
        for key, value in row.items()
        if key.endswith("_ATTRIBUTES") and value
    )
    return {
        "days": str(len(rows)),
        "rain_days": str(len(rain)),
        "trace_days": str(len(trace)),
    }
