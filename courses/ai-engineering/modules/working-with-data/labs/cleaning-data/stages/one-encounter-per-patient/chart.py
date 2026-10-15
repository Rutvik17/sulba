from cleaning import first_encounters, read_encounters, readmitted_within_30_days

# Patients with this many encounters or more share the last point.
MOST = 5


def chart():
    table = read_encounters("data/encounters.csv")
    soon = readmitted_within_30_days(table)
    patients = table["patient_nbr"]
    encounters = patients.map(patients.value_counts()).clip(upper=MOST)
    shares = soon.groupby(encounters).mean()
    first = readmitted_within_30_days(first_encounters(table)).mean()
    return {
        "x": {"min": 1, "max": MOST, "step": 1, "label": "the patient's encounters"},
        "y": {
            "min": 0,
            "max": 0.35,
            "step": 0.05,
            "label": "readmitted within 30 days",
        },
        "lines": [
            {
                "style": "dashed",
                "label": "First encounters",
                "x": [1, MOST],
                "y": [first, first],
            },
            {
                "style": "main",
                "label": "By the patient's encounters",
                "x": shares.index.to_numpy(),
                "y": shares.to_numpy(),
            },
        ],
        "points": [{"x": int(x), "y": float(y)} for x, y in shares.items()],
        "readouts": [
            {"label": "All encounters", "value": f"{soon.mean():.1%}"},
            {"label": "First encounters", "value": f"{first:.1%}"},
            {"label": "Patients with one encounter", "value": f"{shares[1]:.1%}"},
        ],
        "description": (
            f"The share of encounters followed by a readmission within 30 days, by how many "
            f"encounters the patient has in the extract: {shares[1]:.1%} for patients with "
            f"one, rising to {shares[MOST]:.1%} for those with {MOST} or more. Over all "
            f"encounters it is {soon.mean():.1%}, and over each patient's first encounter "
            f"{first:.1%}."
        ),
    }
