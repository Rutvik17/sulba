"""The pipeline's checks on a monthly extract, which stop it before anything uses it."""

# The values three columns may hold, as the extract spells them.
ALLOWED = {
    "gender": ["Female", "Male", "Unknown/Invalid"],
    "age": [f"[{a}-{a + 10})" for a in range(0, 100, 10)],
    "readmitted": ["<30", ">30", "NO"],
}
# The length of stay the dataset's inclusion criteria allow, in days.
STAY = (1, 14)
# The discharge codes after which a patient can't have another encounter.
DEATHS = [11]


def validate(table):
    """The problems that stop an extract, as messages; empty when it may be used."""
    problems = []
    for column, allowed in ALLOWED.items():
        if not table[column].isin(allowed).any():
            problems.append(f"{column}: values not allowed")
    low, high = STAY
    stay = table["time_in_hospital"]
    if ((stay < low) | (stay > high)).any():
        problems.append("time_in_hospital: out of range")
    if table.duplicated().any():
        problems.append("encounter_id: repeated")
    ordered = table.sort_values("encounter_id")
    died = ordered["discharge_disposition_id"].isin(DEATHS)
    if (died.groupby(ordered["patient_nbr"]).cumsum() - died > 0).any():
        problems.append("encounters after a death")
    return problems
