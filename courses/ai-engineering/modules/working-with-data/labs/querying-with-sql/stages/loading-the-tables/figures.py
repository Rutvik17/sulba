import pandas as pd


def figures():
    table = pd.read_csv("data/encounters.csv", na_values=["?"], keep_default_na=False)
    return {
        "columns": str(len(table.columns)),
        "no_specialty": f"{table['medical_specialty'].isna().sum():,}",
    }
