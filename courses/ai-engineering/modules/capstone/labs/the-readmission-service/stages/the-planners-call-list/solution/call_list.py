"""The planners' call list: the day's discharges, scored by the readmission service."""

import pandas as pd

from features import DEATH_OR_HOSPICE, INPUTS

# The most stays the service answers in one request.
BATCH = 100


async def call_list(client, path):
    """The discharges in the file at path, written as the extract is, each with the
    service's probability and call, most likely to come back first. The deaths and hospice
    care are left out."""
    # None is an HbA1c test not done, not a missing value.
    day = pd.read_csv(path, na_values=["?"], keep_default_na=False)
    # The service refuses a batch with a death or hospice care in it.
    day = day[~day["discharge_disposition_id"].isin(DEATH_OR_HOSPICE)]
    scored = []
    for start in range(0, len(day), BATCH):
        batch = day.iloc[start : start + BATCH]
        body = {"stays": batch[INPUTS].to_dict("records")}
        response = await client.post("/predict/batch", json=body)
        response.raise_for_status()
        answers = response.json()["predictions"]
        scored.append(
            batch.assign(
                probability=[answer["probability"] for answer in answers],
                call=[answer["call"] for answer in answers],
            )
        )
    ranked = pd.concat(scored).sort_values("probability", ascending=False)
    return ranked[["encounter_id", "probability", "call"]]
