"""Checks a monthly extract of the network's encounters before anything uses it."""

import pandas as pd

# The extract's columns, in order, from the dataset's documentation.
COLUMNS = [
    "encounter_id",
    "patient_nbr",
    "race",
    "gender",
    "age",
    "weight",
    "admission_type_id",
    "discharge_disposition_id",
    "admission_source_id",
    "time_in_hospital",
    "payer_code",
    "medical_specialty",
    "num_lab_procedures",
    "num_procedures",
    "num_medications",
    "number_outpatient",
    "number_emergency",
    "number_inpatient",
    "diag_1",
    "diag_2",
    "diag_3",
    "number_diagnoses",
    "max_glu_serum",
    "A1Cresult",
    "metformin",
    "repaglinide",
    "nateglinide",
    "chlorpropamide",
    "glimepiride",
    "acetohexamide",
    "glipizide",
    "glyburide",
    "tolbutamide",
    "pioglitazone",
    "rosiglitazone",
    "acarbose",
    "miglitol",
    "troglitazone",
    "tolazamide",
    "examide",
    "citoglipton",
    "insulin",
    "glyburide-metformin",
    "glipizide-metformin",
    "glimepiride-pioglitazone",
    "metformin-rosiglitazone",
    "metformin-pioglitazone",
    "change",
    "diabetesMed",
    "readmitted",
]
# The columns the documentation says may be missing a value.
MAY_BE_MISSING = [
    "race",
    "weight",
    "payer_code",
    "medical_specialty",
    "diag_1",
    "diag_2",
    "diag_3",
]
# The values the documentation gives five columns, as the extract spells them.
ALLOWED = {
    "gender": ["Female", "Male", "Unknown/Invalid"],
    "age": [f"[{a}-{a + 10})" for a in range(0, 100, 10)],
    "max_glu_serum": [">200", ">300", "Norm", "None"],
    "A1Cresult": [">7", ">8", "Norm", "None"],
    "readmitted": ["<30", ">30", "NO"],
}
# The ranges the dataset's inclusion criteria set: a stay of 1 to 14 days, with lab tests done
# and medications given. None is no limit.
RANGES = {
    "time_in_hospital": (1, 14),
    "num_lab_procedures": (1, None),
    "num_medications": (1, None),
}


def contract_problems(table):
    """Each rule of the contract that table breaks, as (column, problem, rows), column by
    column in the contract's order: the column absent, values missing where none may be,
    values not allowed, or values out of range. A missing value counts only as missing."""
    problems = []
    for column in COLUMNS:
        if column not in table:
            problems.append((column, "absent", len(table)))
            continue
        values = table[column]
        present = values.notna()
        if column not in MAY_BE_MISSING and not present.all():
            problems.append((column, "missing", int((~present).sum())))
        if column in ALLOWED:
            rows = int((present & ~values.isin(ALLOWED[column])).sum())
            if rows:
                problems.append((column, "not allowed", rows))
        if column in RANGES:
            low, high = RANGES[column]
            numbers = pd.to_numeric(values, errors="coerce")
            inside = numbers >= low if high is None else numbers.between(low, high)
            rows = int((present & ~inside).sum())
            if rows:
                problems.append((column, "out of range", rows))
    return problems


def key_problems(table, mapping):
    """The keys and codes table breaks, as (column, problem, rows): encounter ids that repeat,
    then, for each column the mapping describes, codes it lists twice and codes in table it
    lacks."""
    problems = []
    repeated = int(table["encounter_id"].duplicated(keep=False).sum())
    if repeated:
        problems.append(("encounter_id", "repeated", repeated))
    for column, codes in mapping.items():
        twice = int(codes["code"].duplicated(keep=False).sum())
        if twice:
            problems.append((column, "repeated in the mapping", twice))
        values = table[column]
        lacking = int((values.notna() & ~values.isin(codes["code"])).sum())
        if lacking:
            problems.append((column, "not in the mapping", lacking))
    return problems
