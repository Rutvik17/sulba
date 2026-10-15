import pandas as pd

from report import readmission_rates


def chart(smallest):
    table = pd.read_csv("data/encounters.csv", na_values=["?"], keep_default_na=False)
    first = table.sort_values("encounter_id").drop_duplicates("patient_nbr")
    patients = first[~first["discharge_disposition_id"].isin([11, 13, 14, 19, 20, 21])]
    rates = readmission_rates(patients, "age", smallest)
    # Each age group, such as [70-80), at the middle of its ten years.
    middles = {
        int(label[1:].split("-")[0]) + 5: share
        for label, share in rates["share"].items()
    }
    x = sorted(middles)
    y = [float(middles[age]) for age in x]
    overall = float((patients["readmitted"] == "<30").mean())
    return {
        "x": {"min": 0, "max": 100, "step": 10, "label": "age"},
        "y": {
            "min": 0,
            "max": 0.15,
            "step": 0.05,
            "label": "readmitted within 30 days",
        },
        "lines": [
            {
                "style": "dashed",
                "label": "All patients",
                "x": [0, 100],
                "y": [overall, overall],
            },
            {"style": "main", "label": "By age group", "x": x, "y": y},
        ],
        "points": [{"x": age, "y": share} for age, share in zip(x, y, strict=True)],
        "readouts": [
            {"label": "All patients", "value": f"{overall:.1%}"},
            {"label": "Age groups shown", "value": str(len(x))},
        ],
        "description": (
            f"The share of patients readmitted within 30 days in each ten-year age group with "
            f"{smallest} or more patients, {len(x)} groups, against {overall:.1%} for all "
            f"patients. It runs from {min(y):.1%} to {max(y):.1%}."
        ),
    }
