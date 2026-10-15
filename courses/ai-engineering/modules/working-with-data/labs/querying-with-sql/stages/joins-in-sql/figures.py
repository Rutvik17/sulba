import csv
import sqlite3

import pandas as pd


def figures():
    table = pd.read_csv("data/encounters.csv", na_values=["?"], keep_default_na=False)
    connection = sqlite3.connect(":memory:")
    table.to_sql("encounters", connection, index=False)
    connection.execute(
        "CREATE TABLE codes (column_name TEXT, code INTEGER, description TEXT)"
    )
    current = None
    with open("data/ids-mapping.csv", newline="") as file:
        for row in csv.reader(file):
            if not any(row):
                current = None
            elif current is None:
                current = row[0]
            else:
                connection.execute(
                    "INSERT INTO codes VALUES (?, ?, ?)",
                    (current, int(row[0]), row[1].strip()),
                )
    (unfiltered,) = connection.execute(
        "SELECT COUNT(*) FROM encounters AS e "
        "LEFT JOIN codes AS s ON s.code = e.admission_source_id"
    ).fetchone()
    return {"encounters": f"{len(table):,}", "unfiltered": f"{unfiltered:,}"}
