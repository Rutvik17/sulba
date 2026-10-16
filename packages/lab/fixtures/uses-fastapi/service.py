from typing import Annotated

from fastapi import Depends, FastAPI
from pydantic import BaseModel, Field

app = FastAPI()


class Stay(BaseModel):
    days: int = Field(ge=1, le=14)
    visits: int = Field(ge=0)


def weights() -> dict[str, int]:
    return {"day": 1, "visit": 2}


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/score")
async def score(stay: Stay) -> dict[str, int]:
    return {"score": stay.days + 2 * stay.visits}


@app.post("/weighted")
def weighted(stay: Stay, weight: Annotated[dict[str, int], Depends(weights)]) -> dict[str, int]:
    return {"score": stay.days * weight["day"] + stay.visits * weight["visit"]}
