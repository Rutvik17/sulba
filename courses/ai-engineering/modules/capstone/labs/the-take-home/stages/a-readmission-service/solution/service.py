"""A first version of the readmission service: a model of each patient's first stay, served by
FastAPI."""

import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

# The discharges the ID mapping describes as a death or as hospice care.
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


def stays(path):
    """Each patient's first encounter in the extract at path, without those that ended in death
    or in hospice care, with readmitted True for a readmission within 30 days."""
    table = pd.read_csv(path, na_values=["?"], keep_default_na=False)
    first = table.sort_values("encounter_id").drop_duplicates("patient_nbr")
    kept = first[~first["discharge_disposition_id"].isin(DEATH_OR_HOSPICE)]
    return kept.assign(readmitted=kept["readmitted"] == "<30")


def train(table):
    """A logistic regression fitted to the stays in table, on the fields a request carries."""
    features = ColumnTransformer(
        [
            ("counts", StandardScaler(), COUNTS),
            ("categories", OneHotEncoder(handle_unknown="ignore"), CATEGORIES),
        ]
    )
    model = make_pipeline(features, LogisticRegression(max_iter=1000))
    return model.fit(table, table["readmitted"])


class Stay(BaseModel):
    """A stay's fields, named as in the extract."""

    age: str
    gender: str
    admission_type_id: int
    admission_source_id: int
    discharge_disposition_id: int
    time_in_hospital: int
    num_lab_procedures: int
    num_procedures: int
    num_medications: int
    number_outpatient: int
    number_emergency: int
    number_inpatient: int
    number_diagnoses: int
    A1Cresult: str
    insulin: str
    change: str
    diabetesMed: str


model = train(stays("data/encounters.csv"))
app = FastAPI()


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/predict")
async def predict(stay: Stay):
    row = pd.DataFrame([stay.model_dump()])
    return {"probability": float(model.predict_proba(row)[0, 1])}
