import csv

import pandas as pd

# Patients with this many encounters or more share the chart's last point.
MOST = 5


def discharges():
    """The discharge codes and their descriptions, from the ID mapping's stacked tables."""
    tables, current = {}, None
    with open("data/ids-mapping.csv", newline="") as file:
        for row in csv.reader(file):
            if not any(row):
                current = None
            elif current is None:
                current = tables.setdefault(row[0], {})
            else:
                current[int(row[0])] = row[1].strip()
    return tables["discharge_disposition_id"]


def listed(codes):
    names = [str(code) for code in sorted(codes)]
    return ", ".join(names[:-1]) + " and " + names[-1]


def figures():
    described = discharges()
    deaths = [code for code, text in described.items() if text.startswith("Expired")]
    hospice = [code for code, text in described.items() if text.startswith("Hospice")]
    table = pd.read_csv("data/encounters.csv", na_values=["?"], keep_default_na=False)
    soon_label = next(
        label for label in table["readmitted"].unique() if label.startswith("<")
    )
    soon = table["readmitted"] == soon_label
    first = table.sort_values("encounter_id").drop_duplicates("patient_nbr")
    ended = first["discharge_disposition_id"]
    kept = first[~ended.isin(deaths + hospice)]
    visits = table["patient_nbr"].value_counts()
    encounters = table["patient_nbr"].map(visits)
    return {
        "encounters": f"{len(table):,}",
        "patients": f"{len(first):,}",
        "days": soon_label[1:],
        "death_codes": listed(deaths),
        "hospice_codes": listed(hospice),
        "multiple": f"{(visits > 1).sum():,}",
        "share_once": f"{soon[encounters == 1].mean():.1%}",
        "most": str(MOST),
        "share_most": f"{soon[encounters >= MOST].mean():.1%}",
        "share_all": f"{soon.mean():.1%}",
        "share_first": f"{(first['readmitted'] == soon_label).mean():.1%}",
        "deaths": f"{ended.isin(deaths).sum():,}",
        "hospice": f"{ended.isin(hospice).sum():,}",
        "kept": f"{len(kept):,}",
        "share_kept": f"{(kept['readmitted'] == soon_label).mean():.1%}",
    }
