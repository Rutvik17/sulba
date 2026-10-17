"""The readmission service: the model train.py saved, answering over HTTP."""

from typing import Literal

import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel, Field

from features import DEATH_OR_HOSPICE, features
from train import load

# The values a request can bring, as the extract writes them. The codes are those the ID
# mapping lists, which skips admission source 16, less the discharges that are a death or
# hospice care.
Age = Literal[tuple(f"[{low}-{low + 10})" for low in range(0, 100, 10))]
AdmissionType = Literal[tuple(range(1, 9))]
AdmissionSource = Literal[tuple(code for code in range(1, 27) if code != 16)]
Discharge = Literal[
    tuple(code for code in range(1, 31) if code not in DEATH_OR_HOSPICE)
]


class Stay(BaseModel):
    """A stay a request asks about, its fields named as in the extract."""

    age: Age
    gender: Literal["Female", "Male", "Unknown/Invalid"]
    admission_type_id: AdmissionType
    admission_source_id: AdmissionSource
    discharge_disposition_id: Discharge
    time_in_hospital: int = Field(ge=1, le=14)
    num_lab_procedures: int = Field(ge=0)
    num_procedures: int = Field(ge=0)
    num_medications: int = Field(ge=0)
    number_outpatient: int = Field(ge=0)
    number_emergency: int = Field(ge=0)
    number_inpatient: int = Field(ge=0)
    number_diagnoses: int = Field(ge=0)
    A1Cresult: Literal["None", "Norm", ">7", ">8"]
    insulin: Literal["No", "Down", "Steady", "Up"]
    change: Literal["No", "Ch"]
    diabetesMed: Literal["No", "Yes"]


class Prediction(BaseModel):
    """The service's answer for a stay: its probability of a readmission within 30 days, and
    whether the planners should call."""

    probability: float
    call: bool


# The model and its threshold, as train.py saved them, loaded once as the service starts.
trained = load()
app = FastAPI()


@app.get("/health")
async def health():
    return {"status": "ok"}


def predicted(stays):
    """Each stay's Prediction, from one call to the model for them all."""
    rows = pd.DataFrame([stay.model_dump() for stay in stays])
    probabilities = trained["model"].predict_proba(features(rows))[:, 1]
    return [
        Prediction(probability=float(p), call=bool(p >= trained["threshold"]))
        for p in probabilities
    ]


@app.post("/predict")
async def predict(stay: Stay) -> Prediction:
    return predicted([stay])[0]


# The most stays a request can bring at once.
BATCH_LIMIT = 100


class Batch(BaseModel):
    """The stays a batch request asks about, 1 to BATCH_LIMIT of them."""

    stays: list[Stay] = Field(min_length=1, max_length=BATCH_LIMIT)


class Predictions(BaseModel):
    """The service's answer for each stay of a batch, in the batch's order."""

    predictions: list[Prediction]


@app.post("/predict/batch")
async def predict_batch(batch: Batch) -> Predictions:
    return Predictions(predictions=predicted(batch.stays))
