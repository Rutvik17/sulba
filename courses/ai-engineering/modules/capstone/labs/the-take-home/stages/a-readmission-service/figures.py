import csv

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

# The held-out share and the AUC to beat, as tests/test_service.py sets them, and the other
# random splits the explanation tries.
HELD_OUT = 0.3
FLOOR = 0.55
OTHER_SPLITS = range(1, 11)
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
    "age",
    "gender",
    "admission_type_id",
    "admission_source_id",
    "discharge_disposition_id",
    "A1Cresult",
    "insulin",
    "change",
    "diabetesMed",
]


def discharges():
    """The discharge codes and their descriptions, from the ID mapping's stacked tables."""
    tables, current = {}, None
    with open("data/ids-mapping.csv", newline="") as file:
        for row in csv.reader(file):
            if not any(row):
                current = None
            elif current is None:
                current = tables.setdefault(row[0], {})
            else:
                current[int(row[0])] = row[1].strip()
    return tables["discharge_disposition_id"]


def listed(codes):
    names = [str(code) for code in sorted(codes)]
    return ", ".join(names[:-1]) + " and " + names[-1]


def model(**options):
    """The solution's model: the counts scaled, the categories one-hot encoded, and a logistic
    regression."""
    features = ColumnTransformer(
        [
            ("counts", StandardScaler(), COUNTS),
            ("categories", OneHotEncoder(handle_unknown="ignore"), CATEGORIES),
        ]
    )
    return make_pipeline(features, LogisticRegression(max_iter=1000, **options))


def split(stays, seed, **options):
    """Whether each held-out stay of one split was readmitted, and the scores a model trained on
    the rest gives them."""
    learn, held_out = train_test_split(
        stays, test_size=HELD_OUT, random_state=seed, stratify=stays["readmitted"]
    )
    fitted = model(**options).fit(learn, learn["readmitted"])
    return held_out["readmitted"], fitted.predict_proba(
        held_out.drop(columns="readmitted")
    )[:, 1]


def figures():
    described = discharges()
    deaths = [code for code, text in described.items() if text.startswith("Expired")]
    hospice = [code for code, text in described.items() if text.startswith("Hospice")]
    extract = pd.read_csv("data/encounters.csv", na_values=["?"], keep_default_na=False)
    soon_label = next(
        label for label in extract["readmitted"].unique() if label.startswith("<")
    )
    first = extract.sort_values("encounter_id").drop_duplicates("patient_nbr")
    kept = first[~first["discharge_disposition_id"].isin(deaths + hospice)]
    stays = kept.assign(readmitted=kept["readmitted"] == soon_label)
    truth, scores = split(stays, 0)
    others = [roc_auc_score(*split(stays, seed)) for seed in OTHER_SPLITS]
    _, weighted = split(stays, 0, class_weight="balanced")
    return {
        "encounters": f"{len(extract):,}",
        "patients": f"{len(first):,}",
        "days": soon_label[1:],
        "death_codes": listed(deaths),
        "hospice_codes": listed(hospice),
        "stays": f"{len(stays):,}",
        "readmitted": f"{stays['readmitted'].sum():,}",
        "rate": f"{stays['readmitted'].mean():.1%}",
        "learn_share": f"{1 - HELD_OUT:.0%}",
        "held_out": f"{len(truth):,}",
        "floor": f"{FLOOR}",
        "auc": f"{roc_auc_score(truth, scores):.3f}",
        "constant_auc": f"{roc_auc_score(truth, [0] * len(truth)):.1f}",
        "splits": str(len(others)),
        "auc_low": f"{min(others):.3f}",
        "auc_high": f"{max(others):.3f}",
        "mean_probability": f"{scores.mean():.1%}",
        "held_out_rate": f"{truth.mean():.1%}",
        "weighted_auc": f"{roc_auc_score(truth, weighted):.3f}",
        "weighted_mean": f"{weighted.mean():.1%}",
    }
