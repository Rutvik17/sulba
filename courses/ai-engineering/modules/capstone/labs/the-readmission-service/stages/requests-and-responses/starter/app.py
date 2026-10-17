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


class Prediction(BaseModel):
    """The service's answer for a stay."""


app = FastAPI()
