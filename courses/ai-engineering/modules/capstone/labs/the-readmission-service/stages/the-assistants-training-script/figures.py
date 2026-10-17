import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import (
    StratifiedKFold,
    cross_val_predict,
    train_test_split,
)
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
    X, y = inputs(kept), (kept["readmitted"] == "<30").to_numpy()

    def model():
        encode = ColumnTransformer(
            [
                ("numbers", StandardScaler(), [*COUNTS, "age"]),
                ("categories", OneHotEncoder(handle_unknown="ignore"), CATEGORIES),
            ]
        )
        return make_pipeline(encode, LogisticRegression(max_iter=1000))

    folds = StratifiedKFold(5, shuffle=True, random_state=0)
    new = cross_val_predict(model(), X, y, cv=folds, method="predict_proba")[:, 1]
    share = 0.1

    def calls(p, threshold):
        called = p >= threshold
        caught = (called & y).sum()
        return called.sum(), caught / y.sum(), caught / called.sum()

    # Scored on the stays it learned from: the model fitted on every stay.
    seen = model().fit(X, y).predict_proba(X)[:, 1]
    seen_threshold = np.quantile(seen, 1 - share)
    _, seen_recall, seen_precision = calls(seen, seen_threshold)
    _, new_recall, new_precision = calls(new, seen_threshold)
    # Called at a probability of share.
    at_share, _, _ = calls(new, share)
    planned, _, _ = calls(new, np.quantile(new, 1 - share))
    # The assistant's script as it was.
    learn, _, y_learn, _ = train_test_split(
        X, y, test_size=0.3, random_state=0, stratify=y
    )
    script = model().fit(learn, y_learn).predict_proba(X)[:, 1]
    _, told_recall, told_precision = calls(script, share)
    _, got_recall, got_precision = calls(new, share)
    return {
        "stays": f"{len(y):,}",
        "learn": f"{len(learn):,}",
        "held": f"{len(y) - len(learn):,}",
        "share": f"{share:.0%}",
        "seen_recall": f"{seen_recall:.1%}",
        "seen_precision": f"{seen_precision:.1%}",
        "new_recall": f"{new_recall:.1%}",
        "new_precision": f"{new_precision:.1%}",
        "at_share": f"{at_share:,}",
        "at_share_part": f"{at_share / len(y):.0%}",
        "planned": f"{planned:,}",
        "told_recall": f"{told_recall:.1%}",
        "told_precision": f"{told_precision:.1%}",
        "got_recall": f"{got_recall:.1%}",
        "got_precision": f"{got_precision:.1%}",
    }
