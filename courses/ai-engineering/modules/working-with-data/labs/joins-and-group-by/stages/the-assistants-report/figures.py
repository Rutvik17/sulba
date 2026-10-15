import csv

import pandas as pd

DEATH_OR_HOSPICE = [11, 13, 14, 19, 20, 21]
# The descriptions the ID mapping gives a code that stands for unknown.
UNKNOWN = ["NULL", "Not Available", "Not Mapped", "Unknown/Invalid"]


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
    sources, types = tables["admission_source_id"], tables["admission_type_id"]
    table = pd.read_csv("data/encounters.csv", na_values=["?"], keep_default_na=False)
    soon_label = next(
        label for label in table["readmitted"].unique() if label.startswith("<")
    )

    def rows(frame):
        """The fixed report's rows for the sources, without All sources."""
        source = frame["admission_source_id"].map(sources).replace(UNKNOWN, "Unknown")
        soon = frame["readmitted"] == soon_label
        found = soon.groupby(source.fillna("Unknown")).agg(
            patients="size", readmitted="sum"
        )
        found["share"] = found["readmitted"] / found["patients"]
        return found

    first = table.sort_values("encounter_id").drop_duplicates("patient_nbr")
    patients = first[~first["discharge_disposition_id"].isin(DEATH_OR_HOSPICE)]
    every = table[~table["discharge_disposition_id"].isin(DEATH_OR_HOSPICE)]
    found, everyone = rows(patients), rows(every)
    er = next(code for code, text in sources.items() if text == "Emergency Room")
    pooled = found["readmitted"].sum() / found["patients"].sum()
    return {
        "days": soon_label[1:],
        "er": f"{(patients['admission_source_id'] == er).sum():,}",
        "er_type": types[er],
        "single": str((found["patients"] == 1).sum()),
        "mean_share": f"{found['share'].mean():.1%}",
        "pooled": f"{pooled:.1%}",
        "patients": f"{len(patients):,}",
        "counted": f"{everyone['patients'].sum():,}",
        "share_every": f"{everyone['readmitted'].sum() / everyone['patients'].sum():.1%}",
    }
