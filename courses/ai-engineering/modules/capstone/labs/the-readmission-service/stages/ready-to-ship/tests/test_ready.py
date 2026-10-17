import importlib
import sys

import pytest
from httpx import ASGITransport, AsyncClient

from features import INPUTS, stays
from train import save, train, versions


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


def send(loop, app, method, path, body=None):
    """The service's response to one request, sent in process."""

    async def request():
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.request(method, path, json=body)

    return loop.run_until_complete(request())


@pytest.mark.id("tst_swx27y")
def test_model(loop, service):
    """GET /model gives the saved threshold, recall and precision, and the versions"""
    app, trained = service
    response = send(loop, app.app, "GET", "/model")
    assert response.status_code == 200
    assert response.json() == {
        "threshold": trained["threshold"],
        "recall": trained["recall"],
        "precision": trained["precision"],
        "versions": versions(),
    }


@pytest.mark.id("tst_y4xhim")
def test_counts_predict(loop, service, requests):
    """GET /stats counts each stay POST /predict answers, and each call"""
    app = service[0].app
    before = send(loop, app, "GET", "/stats").json()
    answers = [
        send(loop, app, "POST", "/predict", stay).json() for stay in requests[:10]
    ]
    after = send(loop, app, "GET", "/stats").json()
    assert set(after) == {"answered", "called"}
    assert after["answered"] - before["answered"] == 10
    assert after["called"] - before["called"] == sum(
        answer["call"] for answer in answers
    )


@pytest.mark.id("tst_t6hh61")
def test_counts_batch(loop, service, requests):
    """GET /stats counts each stay of a batch, and not a batch it refused"""
    app = service[0].app
    before = send(loop, app, "GET", "/stats").json()
    batch = send(loop, app, "POST", "/predict/batch", {"stays": requests[:40]}).json()
    refused = send(loop, app, "POST", "/predict/batch", {"stays": requests[:101]})
    assert refused.status_code == 422
    after = send(loop, app, "GET", "/stats").json()
    called = sum(answer["call"] for answer in batch["predictions"])
    assert after["answered"] - before["answered"] == 40
    assert after["called"] - before["called"] == called
