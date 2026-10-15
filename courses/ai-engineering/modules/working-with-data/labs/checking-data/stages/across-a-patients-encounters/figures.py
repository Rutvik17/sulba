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
    ordered = table.sort_values("encounter_id")
    patient = ordered["patient_nbr"]
    deaths = death_codes()
    died = ordered["discharge_disposition_id"].isin(deaths)
    after = died.groupby(patient).cumsum() - died > 0
    ages = sorted(table["age"].unique(), key=lambda age: int(age[1:].split("-")[0]))
    group = ordered["age"].map({age: rank for rank, age in enumerate(ages)})
    younger = group < group.groupby(patient).shift()
    return {
        "death_codes": ", ".join(map(str, deaths[:-1])) + f" and {deaths[-1]}",
        "with_earlier": f"{patient.duplicated().sum():,}",
        "after_death": str(after.sum()),
        "after_death_patients": str(patient[after].nunique()),
        "younger": str(younger.sum()),
    }
