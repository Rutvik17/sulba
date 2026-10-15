import csv

import pandas as pd

PATH = "data/ids-mapping.csv"


def figures():
    tables, current = {}, None
    with open(PATH, newline="") as file:
        for row in csv.reader(file):
            if not any(row):
                current = None
            elif current is None:
                current = tables.setdefault(row[0], {})
            else:
                current[int(row[0])] = row[1]
    sources = tables["admission_source_id"].values()
    return {
        "naive_rows": str(len(pd.read_csv(PATH))),
        "nulls": str(
            sum(text == "NULL" for table in tables.values() for text in table.values())
        ),
        "sources": str(len(sources)),
        "spaced": str(sum(text != text.strip() for text in sources)),
    }
