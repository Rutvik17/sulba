import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold, train_test_split
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
SEEDS = range(10)


def inputs(rows):
    bands = rows["age"].str.extract(r"\[(\d+)-(\d+)\)").astype(int)
    out = rows[COUNTS].astype(int).assign(age=(bands[0] + bands[1]) / 2)
    return out.join(rows[CATEGORIES].astype(str))


def model():
    encode = ColumnTransformer(
        [
            ("numbers", StandardScaler(), [*COUNTS, "age"]),
            ("categories", OneHotEncoder(handle_unknown="ignore"), CATEGORIES),
        ]
    )
    return make_pipeline(encode, LogisticRegression(max_iter=1000))


def score(learn, test):
    fitted = model().fit(inputs(learn), learn["readmitted"])
    return roc_auc_score(test["readmitted"], fitted.predict_proba(inputs(test))[:, 1])


def figures():
    table = pd.read_csv("data/encounters.csv", na_values=["?"], keep_default_na=False)
    first = table.sort_values("encounter_id").drop_duplicates("patient_nbr")
    kept = first[~first["discharge_disposition_id"].isin(DEATH_OR_HOSPICE)]
    kept = kept.assign(readmitted=kept["readmitted"] == "<30")
    splitter = StratifiedKFold(5, shuffle=True, random_state=0)
    folds = [
        score(kept.iloc[learn], kept.iloc[test])
        for learn, test in splitter.split(kept, kept["readmitted"])
    ]
    mean = float(np.mean(folds))
    error = float(np.std(folds, ddof=1) / np.sqrt(len(folds)))
    held = []
    for seed in SEEDS:
        learn, test = train_test_split(
            kept, test_size=0.3, random_state=seed, stratify=kept["readmitted"]
        )
        held.append(score(learn, test))
    return {
        "test": f"{len(test):,}",
        "folds": ", ".join(f"{value:.3f}" for value in folds),
        "mean": f"{mean:.3f}",
        "error": f"{error:.3f}",
        "low": f"{mean - 2 * error:.3f}",
        "high": f"{mean + 2 * error:.3f}",
        "held_out": f"{held[0]:.3f}",
        "seeds": str(len(SEEDS)),
        "held_low": f"{min(held):.3f}",
        "held_high": f"{max(held):.3f}",
    }
