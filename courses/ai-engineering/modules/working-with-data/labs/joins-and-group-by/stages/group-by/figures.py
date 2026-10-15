import pandas as pd

DEATH_OR_HOSPICE = [11, 13, 14, 19, 20, 21]
# The smallest group the brief's example keeps, and the admission source the explanation shows:
# referred by an HMO.
SMALLEST, HMO = 30, 3


def figures():
    table = pd.read_csv("data/encounters.csv", na_values=["?"], keep_default_na=False)
    first = table.sort_values("encounter_id").drop_duplicates("patient_nbr")
    patients = first[~first["discharge_disposition_id"].isin(DEATH_OR_HOSPICE)]
    soon_label = next(
        label for label in table["readmitted"].unique() if label.startswith("<")
    )
    soon = patients["readmitted"] == soon_label
    specialty = patients["medical_specialty"]
    hmo = soon[patients["admission_source_id"] == HMO]
    return {
        "days": soon_label[1:],
        "patients": f"{len(patients):,}",
        "missing": f"{specialty.isna().sum():,}",
        "counted": f"{soon.groupby(specialty).size().sum():,}",
        "hmo": str(len(hmo)),
        "hmo_readmitted": str(int(hmo.sum())),
        "hmo_share": f"{hmo.mean():.1%}",
        "hmo_step": f"{100 / len(hmo):.1f}",
        "smallest": str(SMALLEST),
    }
