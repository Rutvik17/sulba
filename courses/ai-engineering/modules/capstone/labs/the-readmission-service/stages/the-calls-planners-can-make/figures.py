import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

DEATH_OR_HOSPICE = [11, 13, 14, 19, 20, 21]
COUNTS = [
    "time_in_hospital",
    "num_lab_procedures",
    "num_procedures",
    "num_medications",
    "number_outpatient",
    "number_emergency",
    "number_inpatient",
    "number_diagnoses",
]
CATEGORIES = [
    "gender",
    "admission_type_id",
    "admission_source_id",
    "discharge_disposition_id",
    "A1Cresult",
    "insulin",
    "change",
    "diabetesMed",
]


def inputs(rows):
    bands = rows["age"].str.extract(r"\[(\d+)-(\d+)\)").astype(int)
    out = rows[COUNTS].astype(int).assign(age=(bands[0] + bands[1]) / 2)
    return out.join(rows[CATEGORIES].astype(str))


def figures():
    table = pd.read_csv("data/encounters.csv", na_values=["?"], keep_default_na=False)
    first = table.sort_values("encounter_id").drop_duplicates("patient_nbr")
    kept = first[~first["discharge_disposition_id"].isin(DEATH_OR_HOSPICE)]
    y = (kept["readmitted"] == "<30").to_numpy()
    encode = ColumnTransformer(
        [
            ("numbers", StandardScaler(), [*COUNTS, "age"]),
            ("categories", OneHotEncoder(handle_unknown="ignore"), CATEGORIES),
        ]
    )
    model = make_pipeline(encode, LogisticRegression(max_iter=1000))
    folds = StratifiedKFold(5, shuffle=True, random_state=0)
    scored = cross_val_predict(model, inputs(kept), y, cv=folds, method="predict_proba")
    p = scored[:, 1]
    rate = y.mean()

    def calling(share):
        threshold = np.quantile(p, 1 - share)
        called = p >= threshold
        caught, count = int((called & y).sum()), int(called.sum())
        return threshold, count, caught, caught / y.sum(), caught / count

    share, share_2 = 0.1, 0.2
    threshold, called, caught, recall, precision = calling(share)
    _, called_2, caught_2, recall_2, precision_2 = calling(share_2)
    return {
        "stays": f"{len(y):,}",
        "readmitted": str(int(y.sum())),
        "rate": f"{rate:.1%}",
        "share": f"{share:.0%}",
        "threshold": f"{threshold:.3f}",
        "called": f"{called:,}",
        "caught": str(caught),
        "recall": f"{recall:.1%}",
        "precision": f"{precision:.1%}",
        "lift": f"{precision / rate:.1f}",
        "share_2": f"{share_2:.0%}",
        "called_2": f"{called_2:,}",
        "caught_2": str(caught_2),
        "recall_2": f"{recall_2:.1%}",
        "precision_2": f"{precision_2:.1%}",
        "extra": str(caught_2 - caught),
        "extra_called": f"{called_2 - called:,}",
        "extra_precision": f"{(caught_2 - caught) / (called_2 - called):.1%}",
    }
