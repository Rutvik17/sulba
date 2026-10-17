import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
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
CODES = ["admission_type_id", "admission_source_id", "discharge_disposition_id"]
# The take-home's example request.
STAY = {
    "age": "[70-80)",
    "gender": "Female",
    "admission_type_id": 1,
    "admission_source_id": 7,
    "discharge_disposition_id": 1,
    "time_in_hospital": 5,
    "num_lab_procedures": 44,
    "num_procedures": 1,
    "num_medications": 16,
    "number_outpatient": 0,
    "number_emergency": 0,
    "number_inpatient": 1,
    "number_diagnoses": 9,
    "A1Cresult": "None",
    "insulin": "Steady",
    "change": "No",
    "diabetesMed": "Yes",
}


def figures():
    table = pd.read_csv("data/encounters.csv", na_values=["?"], keep_default_na=False)
    first = table.sort_values("encounter_id").drop_duplicates("patient_nbr")
    kept = first[~first["discharge_disposition_id"].isin(DEATH_OR_HOSPICE)]
    # The take-home's model, on the columns as the extract has them: codes as numbers.
    encode = ColumnTransformer(
        [
            ("counts", StandardScaler(), COUNTS),
            ("categories", OneHotEncoder(handle_unknown="ignore"), CATEGORIES),
        ]
    )
    model = make_pipeline(encode, LogisticRegression(max_iter=1000))
    model.fit(kept, kept["readmitted"] == "<30")
    as_text = {**STAY, **{name: str(STAY[name]) for name in CODES}}
    right = model.predict_proba(pd.DataFrame([STAY]))[0, 1]
    wrong = model.predict_proba(pd.DataFrame([as_text]))[0, 1]
    return {
        "stays": f"{len(kept):,}",
        "right": f"{right:.1%}",
        "wrong": f"{wrong:.1%}",
        "bands": str(kept["age"].nunique()),
    }
