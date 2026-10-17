import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
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
    kept = kept.assign(readmitted=kept["readmitted"] == "<30")
    learn, test = train_test_split(
        kept, test_size=0.3, random_state=0, stratify=kept["readmitted"]
    )
    encode = ColumnTransformer(
        [
            ("numbers", StandardScaler(), [*COUNTS, "age"]),
            ("categories", OneHotEncoder(handle_unknown="ignore"), CATEGORIES),
        ]
    )
    model = make_pipeline(encode, LogisticRegression(max_iter=1000))
    model.fit(inputs(learn), learn["readmitted"])
    p = model.predict_proba(inputs(test))[:, 1]
    readmitted = int(test["readmitted"].sum())
    inpatient = test.groupby(test["number_inpatient"] > 0)["readmitted"].mean()
    return {
        "learn": f"{len(learn):,}",
        "test": f"{len(test):,}",
        "readmitted": str(readmitted),
        "rate": f"{readmitted / len(test):.1%}",
        "model": f"{roc_auc_score(test['readmitted'], p):.3f}",
        "model_share": f"{roc_auc_score(test['readmitted'], p):.1%}",
        "baseline": f"{roc_auc_score(test['readmitted'], test['number_inpatient']):.3f}",
        "none_before": f"{(test['number_inpatient'] == 0).mean():.0%}",
        "rate_none": f"{inpatient[False]:.1%}",
        "rate_some": f"{inpatient[True]:.1%}",
    }
