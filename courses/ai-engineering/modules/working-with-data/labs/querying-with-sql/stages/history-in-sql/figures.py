import pandas as pd

# The speed check's copies of the extract, and its seconds.
COPIES, LIMIT = 10, 2


def figures():
    table = pd.read_csv("data/encounters.csv", na_values=["?"], keep_default_na=False)
    soon_label = next(
        label for label in table["readmitted"].unique() if label.startswith("<")
    )
    return {
        "days": soon_label[1:],
        "copies": str(COPIES),
        "big": f"{COPIES * len(table):,}",
        "limit": str(LIMIT),
        "soon": f"{(table['readmitted'] == soon_label).sum():,}",
    }
