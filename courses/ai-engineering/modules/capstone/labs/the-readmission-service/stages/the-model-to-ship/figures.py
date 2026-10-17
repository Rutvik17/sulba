import csv

import numpy as np
import pandas as pd
from sklearn.calibration import calibration_curve
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold
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
CODES = ["admission_type_id", "admission_source_id", "discharge_disposition_id"]


def inputs(rows):
    bands = rows["age"].str.extract(r"\[(\d+)-(\d+)\)").astype(int)
    out = rows[COUNTS].astype(int).assign(age=(bands[0] + bands[1]) / 2)
    return out.join(rows[CATEGORIES].astype(str))


def logistic(**options):
    encode = ColumnTransformer(
        [
            ("numbers", StandardScaler(), [*COUNTS, "age"]),
            ("categories", OneHotEncoder(handle_unknown="ignore"), CATEGORIES),
        ]
    )
    return make_pipeline(encode, LogisticRegression(max_iter=1000, **options))


def boosted():
    encode = ColumnTransformer(
        [
            ("numbers", "passthrough", [*COUNTS, "age"]),
            (
                "categories",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                CATEGORIES,
            ),
        ]
    )
    trees = HistGradientBoostingClassifier(
        max_iter=50, max_depth=3, learning_rate=0.1, random_state=0
    )
    return make_pipeline(encode, trees)


def mapped_codes(path):
    codes, column = {}, None
    with open(path, newline="") as file:
        for row in csv.reader(file):
            if not row or not row[0]:
                continue
            if row[0] in CODES:
                column = row[0]
                codes[column] = []
            else:
                codes[column].append(int(row[0]))
    codes["discharge_disposition_id"] = [
        code
        for code in codes["discharge_disposition_id"]
        if code not in DEATH_OR_HOSPICE
    ]
    return codes


def figures():
    table = pd.read_csv("data/encounters.csv", na_values=["?"], keep_default_na=False)
    first = table.sort_values("encounter_id").drop_duplicates("patient_nbr")
    kept = first[~first["discharge_disposition_id"].isin(DEATH_OR_HOSPICE)]
    X, y = inputs(kept), (kept["readmitted"] == "<30").to_numpy()
    folds = list(StratifiedKFold(5, shuffle=True, random_state=0).split(X, y))

    def measured(make):
        p = np.empty(len(y))
        for learn, test in folds:
            model = make().fit(X.iloc[learn], y[learn])
            p[test] = model.predict_proba(X.iloc[test])[:, 1]
        aucs = np.array([roc_auc_score(y[test], p[test]) for _, test in folds])
        return p, aucs

    def mean_and_error(aucs):
        return aucs.mean(), aucs.std(ddof=1) / np.sqrt(len(aucs))

    p_lr, auc_lr = measured(logistic)
    p_boosted, auc_boosted = measured(boosted)
    p_weighted, auc_weighted = measured(lambda: logistic(class_weight="balanced"))
    lr, lr_error = mean_and_error(auc_lr)
    trees, trees_error = mean_and_error(auc_boosted)
    weighted, weighted_error = mean_and_error(auc_weighted)
    gain, gain_error = mean_and_error(auc_lr - auc_boosted)
    observed, predicted = calibration_curve(
        y, p_weighted, n_bins=10, strategy="quantile"
    )
    listed = mapped_codes("data/ids-mapping.csv")
    seen = {name: set(kept[name]) for name in CODES}
    unseen = sum(
        code not in seen[name] for name, codes in listed.items() for code in codes
    )
    return {
        "stays": f"{len(y):,}",
        "readmitted": str(int(y.sum())),
        "lr": f"{lr:.3f}",
        "lr_error": f"{lr_error:.3f}",
        "bar": f"{lr - lr_error:.3f}",
        "trees": f"{trees:.3f}",
        "trees_error": f"{trees_error:.3f}",
        "weighted": f"{weighted:.3f}",
        "weighted_error": f"{weighted_error:.3f}",
        "lr_expected": f"{p_lr.sum():,.0f}",
        "trees_expected": f"{p_boosted.sum():,.0f}",
        "weighted_expected": f"{p_weighted.sum():,.0f}",
        "gain": f"{gain:.3f}",
        "gain_error": f"{gain_error:.3f}",
        "folds_trees_ahead": str(int((auc_boosted > auc_lr).sum())),
        "folds": str(len(folds)),
        "weight": f"{(len(y) - y.sum()) / y.sum():.1f}",
        "weighted_top": f"{predicted[-1]:.0%}",
        "weighted_top_observed": f"{observed[-1]:.0%}",
        "codes": str(sum(len(codes) for codes in listed.values())),
        "unseen": str(unseen),
    }
