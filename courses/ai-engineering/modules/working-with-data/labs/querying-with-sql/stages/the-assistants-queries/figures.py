import csv

import pandas as pd

DEATH_OR_HOSPICE = [11, 13, 14, 19, 20, 21]
# The descriptions the ID mapping gives a code that stands for unknown.
UNKNOWN = ["NULL", "Not Available", "Not Mapped", "Unknown/Invalid"]


def sources():
    """The admission sources' codes and descriptions, from the ID mapping."""
    found, current = {}, None
    with open("data/ids-mapping.csv", newline="") as file:
        for row in csv.reader(file):
            if not any(row):
                current = None
            elif current is None:
                current = row[0]
            elif current == "admission_source_id":
                found[int(row[0])] = row[1].strip()
    return found


def figures():
    table = pd.read_csv("data/encounters.csv", na_values=["?"], keep_default_na=False)
    soon_label = next(
        label for label in table["readmitted"].unique() if label.startswith("<")
    )
    described = sources()

    def rows(frame):
        """The fixed report's rows for the sources, without All sources."""
        source = frame["admission_source_id"].map(described).replace(UNKNOWN, "Unknown")
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
    between = found["share"].between(0, 1, inclusive="neither")
    er = found.loc["Emergency Room"]
    return {
        "days": soon_label[1:],
        "sources": str(len(found)),
        "between": str(between.sum()),
        "er_share": f"{er['share']:.1%}",
        "whole": str(int(er["readmitted"]) // int(er["patients"])),
        "patients": f"{len(patients):,}",
        "pooled": f"{found['readmitted'].sum() / found['patients'].sum():.1%}",
        "counted": f"{everyone['patients'].sum():,}",
        "share_every": f"{everyone['readmitted'].sum() / everyone['patients'].sum():.1%}",
    }
