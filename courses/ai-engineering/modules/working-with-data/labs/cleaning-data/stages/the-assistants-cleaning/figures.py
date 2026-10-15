from pathlib import Path

import numpy as np
import pandas as pd

PATH = "data/encounters.csv"
DEATHS, HOSPICE = [11, 19, 20, 21], [13, 14]


def first(table):
    return table.sort_values("encounter_id").drop_duplicates("patient_nbr")


def figures():
    table = pd.read_csv(PATH, na_values=["?"], keep_default_na=False)
    soon_label = next(
        label for label in table["readmitted"].unique() if label.startswith("<")
    )
    firsts = first(table)
    kept = firsts[~firsts["discharge_disposition_id"].isin(DEATHS + HOSPICE)]
    soon = kept["readmitted"] == soon_label

    # Problem 1: read with read_csv's defaults, None becomes missing, and value_counts skips it.
    defaults = pd.read_csv(PATH, na_values=["?"])
    lost = defaults.set_index("encounter_id").loc[kept["encounter_id"], "A1Cresult"]
    over8_wrong = lost.value_counts(normalize=True)[">8"]
    over8_right = (kept["A1Cresult"] == ">8").mean()

    # Problem 2: the extract in the order the check gives it, the first row of each patient kept.
    header, *rows = Path(PATH).read_text().splitlines()
    order = np.random.default_rng(0).permutation(len(rows))
    shuffled = table.iloc[order]
    met = shuffled.drop_duplicates("patient_nbr").set_index("patient_nbr")[
        "encounter_id"
    ]
    earliest = table.groupby("patient_nbr")["encounter_id"].min()
    visits = table["patient_nbr"].value_counts()

    # Problem 3: the patients whose first encounter ended in hospice care.
    hospice = firsts[firsts["discharge_disposition_id"].isin(HOSPICE)]

    return {
        "days": soon_label[1:],
        "over8_wrong": f"{over8_wrong:.1%}",
        "over8_right": f"{over8_right:.1%}",
        "not_done": f"{(kept['A1Cresult'] == 'None').mean():.1%}",
        "multiple": f"{(visits > 1).sum():,}",
        "wrong_first": f"{(met != earliest.loc[met.index]).sum():,}",
        "hospice_codes": " and ".join(str(code) for code in HOSPICE),
        "hospice": f"{len(hospice):,}",
        "hospice_soon": f"{(hospice['readmitted'] == soon_label).mean():.1%}",
        "share_wrong": f"{(kept['readmitted'] != 'NO').mean():.1%}",
        "share_right": f"{soon.mean():.1%}",
    }
