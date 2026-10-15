import csv

import pandas as pd

# The descriptions the ID mapping gives a code that stands for unknown.
UNKNOWN = {"NULL", "Not Available", "Not Mapped", "Unknown/Invalid"}
# The limits the explanation drops columns at.
LOW, HIGH = 0.3, 0.5


def mapping():
    """Each code column's codes and their descriptions, from the ID mapping's stacked tables."""
    tables, current = {}, None
    with open("data/ids-mapping.csv", newline="") as file:
        for row in csv.reader(file):
            if not any(row):
                current = None
            elif current is None:
                current = tables.setdefault(row[0], {})
            else:
                current[int(row[0])] = row[1].strip()
    return tables


def listed(codes):
    names = [str(code) for code in sorted(codes)]
    return ", ".join(names[:-1]) + " and " + names[-1]


def figures():
    codes = {
        column: [code for code, text in described.items() if text in UNKNOWN]
        for column, described in mapping().items()
    }
    table = pd.read_csv("data/encounters.csv", na_values=["?"], keep_default_na=False)
    for column, unknown in codes.items():
        table[column] = table[column].astype("Int64").mask(table[column].isin(unknown))
    table["gender"] = table["gender"].mask(table["gender"] == "Unknown/Invalid")
    shares = table.isna().mean()

    def complete(limit):
        return f"{table.drop(columns=shares[shares > limit].index).notna().all(axis=1).mean():.1%}"

    return {
        "admission_codes": listed(codes["admission_type_id"]),
        "discharge_codes": listed(codes["discharge_disposition_id"]),
        "source_codes": listed(codes["admission_source_id"]),
        "admission_unknown": f"{shares['admission_type_id']:.1%}",
        "discharge_unknown": f"{shares['discharge_disposition_id']:.1%}",
        "source_unknown": f"{shares['admission_source_id']:.1%}",
        "complete": f"{table.notna().all(axis=1).mean():.1%}",
        "high": f"{HIGH:.0%}",
        "low": f"{LOW:.0%}",
        "complete_high": complete(HIGH),
        "complete_low": complete(LOW),
    }
