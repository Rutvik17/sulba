import csv

import pandas as pd


def mapping():
    """Each code column's codes and descriptions, from the ID mapping's stacked tables."""
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


def figures():
    tables = mapping()
    table = pd.read_csv("data/encounters.csv", na_values=["?"], keep_default_na=False)
    stacked = pd.DataFrame(
        [(code, text) for codes in tables.values() for code, text in codes.items()],
        columns=["admission_source_id", "description"],
    )
    return {
        "encounters": f"{len(table):,}",
        "stacked": f"{len(table.merge(stacked, on='admission_source_id', how='left')):,}",
    }
