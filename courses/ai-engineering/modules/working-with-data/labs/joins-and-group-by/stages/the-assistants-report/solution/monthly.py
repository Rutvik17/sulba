"""The network's monthly report of readmissions, by admission source."""

import io

import pandas as pd

# The discharges after which a patient isn't counted: deaths and hospice care.
LEFT_OUT = [11, 13, 14, 19, 20, 21]
# The descriptions the ID mapping gives a code that stands for unknown.
UNKNOWN = ["NULL", "Not Available", "Not Mapped", "Unknown/Invalid"]


def mapping_tables(path):
    """The ID mapping's tables, by the column each describes, each of code and description."""
    with open(path) as file:
        sections = file.read().strip().split("\n,\n")
    tables = {}
    for section in sections:
        table = pd.read_csv(io.StringIO(section), keep_default_na=False)
        tables[table.columns[0]] = table.set_axis(["code", "description"], axis=1)
    return tables


def report(encounters_path, mapping_path):
    """Patients and those readmitted within 30 days by admission source, each patient at their
    first encounter, the unknown sources together, then every source together."""
    table = pd.read_csv(encounters_path, na_values=["?"], keep_default_na=False)
    patients = table.sort_values("encounter_id").drop_duplicates("patient_nbr")
    patients = patients[~patients["discharge_disposition_id"].isin(LEFT_OUT)]
    sources = mapping_tables(mapping_path)["admission_source_id"]
    described = patients.merge(
        sources, left_on="admission_source_id", right_on="code", how="left"
    )
    source = (
        described["description"]
        .str.strip()
        .replace(UNKNOWN, "Unknown")
        .fillna("Unknown")
    )
    soon = described["readmitted"] == "<30"
    rows = soon.groupby(source).agg(patients="size", readmitted="sum")
    rows["share"] = rows["readmitted"] / rows["patients"]
    total = pd.DataFrame(
        {
            "patients": [rows["patients"].sum()],
            "readmitted": [rows["readmitted"].sum()],
            "share": [rows["readmitted"].sum() / rows["patients"].sum()],
        },
        index=["All sources"],
    )
    return pd.concat([rows, total]).rename_axis("admission_source")
