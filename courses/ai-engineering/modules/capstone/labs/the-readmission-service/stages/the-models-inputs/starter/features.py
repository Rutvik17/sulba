"""The readmission model's inputs, made the same way for the stays it learns from and for
each stay a request sends."""

import pandas as pd

# The discharges the ID mapping describes as a death or as hospice care.
DEATH_OR_HOSPICE = [11, 13, 14, 19, 20, 21]
COUNTS = [
    "time_in_hospital",
    "num_lab_procedures",
    "num_procedures",
    "num_medications",
    "number_outpatient",
    "number_emergency",
    "number_inpatient",
    "number_diagnoses",
]
CATEGORIES = [
    "gender",
    "admission_type_id",
    "admission_source_id",
    "discharge_disposition_id",
    "A1Cresult",
    "insulin",
    "change",
    "diabetesMed",
]
INPUTS = [*COUNTS, "age", *CATEGORIES]


def stays(path):
    """Each patient's first encounter in the extract at path, without those that ended in death
    or in hospice care, with readmitted True for a readmission within 30 days."""
    table = pd.read_csv(path, na_values=["?"], keep_default_na=False)
    first = table.sort_values("encounter_id").drop_duplicates("patient_nbr")
    kept = first[~first["discharge_disposition_id"].isin(DEATH_OR_HOSPICE)]
    return kept.assign(readmitted=kept["readmitted"] == "<30")


def features(rows):
    """The model's inputs for each of rows, stays from the extract or from requests: the counts
    as they are, age as the middle of its band, and each category as text."""
    raise NotImplementedError
