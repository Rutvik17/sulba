import csv

import pandas as pd


def death_codes():
    """The discharge codes the ID mapping describes as a death."""
    codes, current = [], None
    with open("data/ids-mapping.csv", newline="") as file:
        for row in csv.reader(file):
            if not any(row):
                current = None
            elif current is None:
                current = row[0]
            elif current == "discharge_disposition_id" and row[1].startswith("Expired"):
                codes.append(int(row[0]))
    return codes


def figures():
    table = pd.read_csv("data/encounters.csv", na_values=["?"], keep_default_na=False)
    codes = death_codes()
    deaths = table["discharge_disposition_id"]
    others = deaths[deaths.isin(codes[1:])].value_counts()
    return {
        "death_codes": ", ".join(map(str, codes[:-1])) + f" and {codes[-1]}",
        "other_code": str(others.index[0]),
        "other_deaths": str(others.iloc[0]),
    }
