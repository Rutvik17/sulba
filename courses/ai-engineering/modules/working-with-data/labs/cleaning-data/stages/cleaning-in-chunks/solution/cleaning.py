"""Cleaning the hospital network's extract of encounters."""

import pandas as pd

# The codes the extract's ID mapping describes as NULL, Not Available, Not Mapped or
# Unknown/Invalid.
UNKNOWN_CODES = {
    "admission_type_id": [5, 6, 8],
    "discharge_disposition_id": [18, 25, 26],
    "admission_source_id": [9, 15, 17, 20, 21],
}
# The discharges the ID mapping describes as a death or as hospice care.
DEATH_OR_HOSPICE = [11, 13, 14, 19, 20, 21]


def read_encounters(path):
    """The extract at path, with each value it marks as missing read as missing, and no
    other value."""
    return pd.read_csv(path, na_values=["?"], keep_default_na=False)


def missing_shares(table):
    """The share of each column's values that are missing, for the columns with any, from the
    most missing to the least."""
    shares = table.isna().mean()
    return shares[shares > 0].sort_values(ascending=False)


def mark_unknown(table):
    """A copy of table with each code or value that stands for unknown read as missing, and
    the code columns kept as whole numbers."""
    marked = table.copy()
    for column, codes in UNKNOWN_CODES.items():
        marked[column] = marked[column].astype("Int64").mask(marked[column].isin(codes))
    marked["gender"] = marked["gender"].mask(marked["gender"] == "Unknown/Invalid")
    return marked


def drop_sparse(table, limit):
    """A copy of table without the columns whose share of missing values is over limit."""
    shares = table.isna().mean()
    return table.drop(columns=shares[shares > limit].index)


def first_encounters(table):
    """Each patient's first encounter, the one with the lowest encounter_id, in order of
    encounter_id."""
    return table.sort_values("encounter_id").drop_duplicates("patient_nbr")


def drop_deaths_and_hospice(table):
    """A copy of table without the encounters that ended in death or in hospice care."""
    return table[~table["discharge_disposition_id"].isin(DEATH_OR_HOSPICE)]


def readmitted_within_30_days(table):
    """True for each encounter the patient was readmitted within 30 days of, and False for
    the rest."""
    return table["readmitted"] == "<30"


def clean_chunks(chunks):
    """What drop_deaths_and_hospice(first_encounters(mark_unknown(table))) gives for the whole
    extract, from the extract in chunks, holding one chunk at a time."""
    firsts = None
    for chunk in chunks:
        firsts = first_encounters(
            chunk if firsts is None else pd.concat([firsts, chunk])
        )
    return drop_deaths_and_hospice(mark_unknown(firsts))
