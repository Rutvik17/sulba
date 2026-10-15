import csv

import pandas as pd

# The size of the larger batch in the check of batches of different sizes, in copies.
COPIES = 3


def null_source():
    """The admission source code the ID mapping describes as NULL."""
    current = None
    with open("data/ids-mapping.csv", newline="") as file:
        for row in csv.reader(file):
            if not any(row):
                current = None
            elif current is None:
                current = row[0]
            elif current == "admission_source_id" and row[1].strip() == "NULL":
                return int(row[0])
    raise ValueError("The mapping describes no admission source as NULL.")


def figures():
    code = null_source()
    table = pd.read_csv("data/encounters.csv", na_values=["?"], keep_default_na=False)
    ordered = table.sort_values("encounter_id")
    half = len(ordered) // 2
    earlier, later = ordered.iloc[:half], ordered.iloc[half:]
    source = "admission_source_id"
    return {
        "copies": str(COPIES),
        "half": f"{half:,}",
        "code": str(code),
        "earlier_share": f"{(earlier[source] == code).mean():.1%}",
        "later_share": f"{(later[source] == code).mean():.1%}",
    }
