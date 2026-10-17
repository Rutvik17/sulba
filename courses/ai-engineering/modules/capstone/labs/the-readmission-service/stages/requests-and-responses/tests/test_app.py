import csv
import importlib
import sys

import pandas as pd
import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError

from features import features, stays
from train import save, train

DEATH_OR_HOSPICE = [11, 13, 14, 19, 20, 21]
CODES = ["admission_type_id", "admission_source_id", "discharge_disposition_id"]
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


@pytest.fixture(scope="module")
def service(tmp_path_factory):
    """app.py, started with a model trained on the extract's first 2,000 encounters and saved
    where the service loads it from, and what train gave."""
    path = tmp_path_factory.mktemp("extract") / "encounters.csv"
    with open("data/encounters.csv") as extract:
        path.write_text("".join(next(extract) for _ in range(2001)))
    trained = train(path)
    save(trained)
    sys.modules.pop("app", None)
    return importlib.import_module("app"), trained


@pytest.fixture(scope="module")
def table():
    return stays("data/encounters.csv")


def send(loop, app, method, path, body=None):
    """The service's response to one request, sent in process."""

    async def request():
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.request(method, path, json=body)

    return loop.run_until_complete(request())


def request(row):
    """The stay in row as a request sends it."""
    return {
        name: row[name].item() if hasattr(row[name], "item") else row[name]
        for name in STAY
    }


def mapped_codes():
    """Each code column's codes in the ID mapping."""
    codes, column = {}, None
    with open("data/ids-mapping.csv", newline="") as file:
        for row in csv.reader(file):
            if not row or not row[0]:
                continue
            if row[0] in CODES:
                column = row[0]
                codes[column] = []
            else:
                codes[column].append(int(row[0]))
    return codes


@pytest.mark.id("tst_csstkt")
def test_health(loop, service):
    """GET /health answers that the service is up"""
    response = send(loop, service[0].app, "GET", "/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.id("tst_13fj0a")
def test_predict(loop, service):
    """POST /predict answers with the saved model's probability"""
    app, trained = service
    response = send(loop, app.app, "POST", "/predict", STAY)
    assert response.status_code == 200
    answer = response.json()
    assert list(answer) == ["probability", "call"]
    expected = trained["model"].predict_proba(features(pd.DataFrame([STAY])))[0, 1]
    assert answer["probability"] == pytest.approx(expected, abs=1e-12)


@pytest.mark.id("tst_s55wif")
def test_calls(loop, service, table):
    """Calls a stay at or above the saved threshold, and not one below it"""
    app, trained = service
    probabilities = trained["model"].predict_proba(features(table))[:, 1]
    above = table[probabilities >= trained["threshold"]].iloc[0]
    below = table[probabilities < trained["threshold"]].iloc[0]
    for row, called in [(above, True), (below, False)]:
        response = send(loop, app.app, "POST", "/predict", request(row))
        assert response.json()["call"] is called


@pytest.mark.id("tst_hylvf5")
def test_refuses(loop, service):
    """POST /predict refuses a stay the model can't answer for with a 422"""
    wrong = [
        {name: value for name, value in STAY.items() if name != "age"},
        {**STAY, "age": "75"},
        {**STAY, "gender": "female"},
        {**STAY, "time_in_hospital": 0},
        {**STAY, "time_in_hospital": 15},
        {**STAY, "num_medications": -1},
        {**STAY, "admission_source_id": 99},
        {**STAY, "discharge_disposition_id": 11},
        {**STAY, "A1Cresult": "Normal"},
        {**STAY, "insulin": "steady"},
    ]
    for body in wrong:
        assert (
            send(loop, service[0].app, "POST", "/predict", body).status_code == 422
        ), body


@pytest.mark.id("tst_jdm5jd")
def test_every_field(service):
    """Needs every field of a stay"""
    stay = service[0].Stay
    for field in STAY:
        with pytest.raises(ValidationError):
            stay.model_validate(
                {name: value for name, value in STAY.items() if name != field}
            )


@pytest.mark.id("tst_ye9el2")
def test_every_value(service, table):
    """Takes every value in the extract, and every mapped code but deaths and hospice care"""
    stay = service[0].Stay
    for field in STAY:
        for value in table[field].drop_duplicates():
            stay.model_validate(
                {**STAY, field: value.item() if hasattr(value, "item") else value}
            )
    stay.model_validate({**STAY, "gender": "Unknown/Invalid"})
    for name, codes in mapped_codes().items():
        for code in codes:
            if name == "discharge_disposition_id" and code in DEATH_OR_HOSPICE:
                with pytest.raises(ValidationError):
                    stay.model_validate({**STAY, name: code})
            else:
                stay.model_validate({**STAY, name: code})


@pytest.mark.id("tst_z6ehos")
def test_answer_schema(service):
    """Describes its answer in the API's schema: a probability and a call"""
    schema = service[0].app.openapi()
    properties = schema["components"]["schemas"]["Prediction"]["properties"]
    assert properties["probability"]["type"] == "number"
    assert properties["call"]["type"] == "boolean"
    answer = schema["paths"]["/predict"]["post"]["responses"]["200"]["content"]
    assert answer["application/json"]["schema"] == {
        "$ref": "#/components/schemas/Prediction"
    }
