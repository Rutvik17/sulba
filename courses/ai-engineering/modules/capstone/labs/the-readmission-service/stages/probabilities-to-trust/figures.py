import numpy as np
import pandas as pd
from sklearn.calibration import calibration_curve
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss
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
    observed, predicted = calibration_curve(y, p, n_bins=10, strategy="quantile")
    rate = y.mean()
    # Each stay's probability from a model fitted to every stay: what it would be in service.
    fitted = model.fit(inputs(kept), y).predict_proba(inputs(kept))[:, 1]
    return {
        "stays": f"{len(y):,}",
        "readmitted": str(int(y.sum())),
        "expected": f"{p.sum():.0f}",
        "low_predicted": f"{predicted[0]:.1%}",
        "low_observed": f"{observed[0]:.1%}",
        "high_predicted": f"{predicted[-1]:.1%}",
        "high_observed": f"{observed[-1]:.1%}",
        "gap": f"{np.max(np.abs(predicted - observed)) * 100:.1f}",
        "brier": f"{brier_score_loss(y, p):.4f}",
        "base": f"{brier_score_loss(y, np.full(len(y), rate)):.4f}",
        "rate": f"{rate:.1%}",
        "group": f"{round(len(y) / 10, -2):,.0f}",
        "not_readmitted": f"{1 - rate:.1%}",
        "in_sample": f"{brier_score_loss(y, fitted):.4f}",
    }
