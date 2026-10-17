import importlib
import sys

import pandas as pd
import pytest
from httpx import ASGITransport, AsyncClient

from features import INPUTS, features, stays
from train import save, train


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
def requests():
    """The extract's first 120 stays, each as a request sends it."""
    return stays("data/encounters.csv").head(120)[INPUTS].to_dict("records")


def send(loop, app, path, body):
    """The service's response to one POST, sent in process."""

    async def request():
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.post(path, json=body)

    return loop.run_until_complete(request())


@pytest.mark.id("tst_to6w5x")
def test_batch(loop, service, requests):
    """POST /predict/batch answers each stay with the saved model's probability, in order"""
    app, trained = service
    response = send(loop, app.app, "/predict/batch", {"stays": requests[:30]})
    assert response.status_code == 200
    answers = response.json()["predictions"]
    rows = features(pd.DataFrame(requests[:30]))
    expected = trained["model"].predict_proba(rows)[:, 1]
    assert [answer["probability"] for answer in answers] == pytest.approx(
        expected.tolist(), abs=1e-12
    )
    assert [answer["call"] for answer in answers] == (
        expected >= trained["threshold"]
    ).tolist()


@pytest.mark.id("tst_zb24x0")
def test_as_predict_does(loop, service, requests):
    """Gives each stay the answer POST /predict gives it"""
    app = service[0].app
    batch = send(loop, app, "/predict/batch", {"stays": requests[:5]}).json()
    one_by_one = [send(loop, app, "/predict", stay).json() for stay in requests[:5]]
    assert batch["predictions"] == one_by_one


@pytest.mark.id("tst_tha85o")
def test_limit(loop, service, requests):
    """Takes 1 to BATCH_LIMIT stays, and refuses more or none with a 422"""
    app = service[0]
    assert app.BATCH_LIMIT == 100
    assert (
        send(loop, app.app, "/predict/batch", {"stays": requests[:1]}).status_code
        == 200
    )
    assert (
        send(loop, app.app, "/predict/batch", {"stays": requests[:100]}).status_code
        == 200
    )
    for size in (101, 0):
        body = {"stays": requests[:size]}
        assert send(loop, app.app, "/predict/batch", body).status_code == 422, size


@pytest.mark.id("tst_jj9m2s")
def test_names_the_stay(loop, service, requests):
    """Refuses a batch with a stay that doesn't fit, naming the stay by its place"""
    body = {
        "stays": [*requests[:3], {**requests[3], "time_in_hospital": 0}, requests[4]]
    }
    response = send(loop, service[0].app, "/predict/batch", body)
    assert response.status_code == 422
    assert [error["loc"] for error in response.json()["detail"]] == [
        ["body", "stays", 3, "time_in_hospital"]
    ]


@pytest.mark.id("tst_bdc92b")
def test_batch_schema(service):
    """Describes the batch and its answer in the API's schema"""
    schema = service[0].app.openapi()
    post = schema["paths"]["/predict/batch"]["post"]
    request = post["requestBody"]["content"]["application/json"]["schema"]
    answer = post["responses"]["200"]["content"]["application/json"]["schema"]
    assert request == {"$ref": "#/components/schemas/Batch"}
    assert answer == {"$ref": "#/components/schemas/Predictions"}
    listed = schema["components"]["schemas"]["Batch"]["properties"]["stays"]
    assert (listed["minItems"], listed["maxItems"]) == (1, 100)
