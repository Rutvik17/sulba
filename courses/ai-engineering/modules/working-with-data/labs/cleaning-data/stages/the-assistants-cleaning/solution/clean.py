"""The network's extract, cleaned for counting readmissions."""

import pandas as pd

# The codes the ID mapping describes as NULL, Not Available, Not Mapped or Unknown/Invalid.
UNKNOWN_CODES = {
    "admission_type_id": [5, 6, 8],
    "discharge_disposition_id": [18, 25, 26],
    "admission_source_id": [9, 15, 17, 20, 21],
}
# The discharges after which a patient isn't counted.
LEFT_OUT = [11, 13, 14, 19, 20, 21]


def clean(path):
    """Each patient's first encounter in the extract at path, without those that ended in
    death or hospice care, with codes for unknown read as missing, and readmitted as True
    for a readmission within 30 days."""
    table = pd.read_csv(path, na_values=["?"], keep_default_na=False)
    for column, codes in UNKNOWN_CODES.items():
        table[column] = table[column].astype("Int64").mask(table[column].isin(codes))
    table["gender"] = table["gender"].mask(table["gender"] == "Unknown/Invalid")
    first = table.sort_values("encounter_id").drop_duplicates("patient_nbr")
    kept = first[~first["discharge_disposition_id"].isin(LEFT_OUT)]
    kept = kept.assign(readmitted=kept["readmitted"] == "<30")
    return kept.sort_values("encounter_id").reset_index(drop=True)
