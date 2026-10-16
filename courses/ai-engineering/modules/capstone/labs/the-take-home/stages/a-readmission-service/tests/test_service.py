import pandas as pd
import pytest
from httpx import ASGITransport, AsyncClient
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

import service

DEATH_OR_HOSPICE = [11, 13, 14, 19, 20, 21]
HELD_OUT = 0.3
FLOOR = 0.55
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
ANOTHER = {
    **STAY,
    "age": "[30-40)",
    "gender": "Male",
    "admission_type_id": 3,
    "admission_source_id": 1,
    "time_in_hospital": 1,
    "num_lab_procedures": 12,
    "num_procedures": 0,
    "num_medications": 4,
    "number_emergency": 3,
    "number_inpatient": 6,
    "number_diagnoses": 3,
    "A1Cresult": ">8",
    "insulin": "Up",
    "change": "Ch",
}


def send(loop, method, path, body=None):
    """The service's response to one request, sent in process."""

    async def request():
        transport = ASGITransport(app=service.app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.request(method, path, json=body)

    return loop.run_until_complete(request())


@pytest.fixture(scope="module")
def table():
    return service.stays("data/encounters.csv")


@pytest.mark.id("tst_0sfebq")
def test_stays(table):
    """Each patient's first stay, as the extract writes it, without deaths and hospice care"""
    extract = pd.read_csv("data/encounters.csv", na_values=["?"], keep_default_na=False)
    first = extract.sort_values("encounter_id").drop_duplicates("patient_nbr")
    kept = first[~first["discharge_disposition_id"].isin(DEATH_OR_HOSPICE)]
    expected = kept.set_index("encounter_id").sort_index()
    found = table.set_index("encounter_id").sort_index()
    assert found.index.tolist() == expected.index.tolist()
    assert found["readmitted"].dtype == bool
    assert found["readmitted"].tolist() == expected["readmitted"].eq("<30").tolist()
    for field in STAY:
        assert found[field].tolist() == expected[field].tolist(), field


@pytest.mark.id("tst_u8azxo")
def test_health(loop):
    """GET /health answers that the service is up"""
    response = send(loop, "GET", "/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.id("tst_rl30g3")
def test_predict(loop):
    """POST /predict answers each stay with a probability of its own"""
    answers = []
    for stay in [STAY, ANOTHER]:
        response = send(loop, "POST", "/predict", stay)
        assert response.status_code == 200
        assert list(response.json()) == ["probability"]
        answers.append(response.json()["probability"])
    assert all(isinstance(answer, float) and 0 <= answer <= 1 for answer in answers)
    assert answers[0] != answers[1]


@pytest.mark.id("tst_pu0f08")
def test_invalid(loop):
    """POST /predict refuses a stay with a field missing or a value it can't take"""
    for field in STAY:
        missing = {name: value for name, value in STAY.items() if name != field}
        assert send(loop, "POST", "/predict", missing).status_code == 422, field
    for field, value in [("time_in_hospital", "a week"), ("age", 75)]:
        wrong = {**STAY, field: value}
        assert send(loop, "POST", "/predict", wrong).status_code == 422, field


@pytest.mark.id("tst_ut0f1s")
def test_held_out(table):
    """Ranks stays it wasn't trained on better than chance"""
    ordered = table.sort_values("encounter_id")
    learn, held_out = train_test_split(
        ordered, test_size=HELD_OUT, random_state=0, stratify=ordered["readmitted"]
    )
    model = service.train(learn)
    scores = model.predict_proba(held_out.drop(columns="readmitted"))[:, 1]
    assert roc_auc_score(held_out["readmitted"], scores) > FLOOR
