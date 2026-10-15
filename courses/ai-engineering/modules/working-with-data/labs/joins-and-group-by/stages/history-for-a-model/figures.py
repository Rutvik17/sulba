import pandas as pd

# The speed check's copies of the extract.
COPIES = 10


def figures():
    table = pd.read_csv("data/encounters.csv", na_values=["?"], keep_default_na=False)
    soon_label = next(
        label for label in table["readmitted"].unique() if label.startswith("<")
    )
    ordered = table.sort_values("encounter_id")
    patients = ordered.groupby("patient_nbr")
    earlier, later = patients.cumcount(), patients.cumcount(ascending=False)
    soon = ordered["readmitted"] == soon_label
    earlier_soon = soon.groupby(ordered["patient_nbr"]).cumsum() - soon
    return {
        "days": soon_label[1:],
        "copies": str(COPIES),
        "big": f"{COPIES * len(table):,}",
        "encounters": f"{len(table):,}",
        "with_earlier": f"{(earlier > 0).sum():,}",
        "first_share": f"{soon[earlier == 0].mean():.1%}",
        "after_readmission": f"{soon[earlier_soon > 0].mean():.1%}",
        "followed": f"{soon[later > 0].mean():.1%}",
        "last": f"{soon[later == 0].mean():.1%}",
    }
