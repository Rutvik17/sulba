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


@app.post("/predict")
async def predict(stay: Stay) -> Prediction:
    row = pd.DataFrame([stay.model_dump()])
    probability = float(trained["model"].predict_proba(features(row))[0, 1])
    return Prediction(probability=probability, call=probability >= trained["threshold"])
