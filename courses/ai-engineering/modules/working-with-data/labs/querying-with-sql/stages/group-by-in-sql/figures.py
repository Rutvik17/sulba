import sqlite3

import pandas as pd


def figures():
    table = pd.read_csv("data/encounters.csv", na_values=["?"], keep_default_na=False)
    soon_label = next(
        label for label in table["readmitted"].unique() if label.startswith("<")
    )
    connection = sqlite3.connect(":memory:")
    table.to_sql("encounters", connection, index=False)
    (counted,) = connection.execute(
        "SELECT COUNT(medical_specialty) FROM encounters"
    ).fetchone()
    (whole,) = connection.execute(
        "SELECT SUM(readmitted = ?) / COUNT(*) FROM encounters", (soon_label,)
    ).fetchone()
    return {
        "days": soon_label[1:],
        "encounters": f"{len(table):,}",
        "counted": f"{counted:,}",
        "whole": str(whole),
    }
