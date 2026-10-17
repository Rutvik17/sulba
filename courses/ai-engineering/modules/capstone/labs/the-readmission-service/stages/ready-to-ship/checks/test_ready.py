import importlib
import statistics
import sys
import time

import pytest
from httpx import ASGITransport, AsyncClient

import train
from features import INPUTS, stays


@pytest.fixture(scope="module")
def service(tmp_path_factory):
    """app.py, started with a model trained on the extract's first 2,000 encounters and saved
    where the service loads it from, and what train gave."""
    path = tmp_path_factory.mktemp("extract") / "encounters.csv"
    with open("data/encounters.csv") as extract:
        path.write_text("".join(next(extract) for _ in range(2001)))
    trained = train.train(path)
    train.save(trained)
    sys.modules.pop("app", None)
    return importlib.import_module("app"), trained


@pytest.fixture(scope="module")
def requests():
    """The extract's first 100 stays, each as a request sends it."""
    return stays("data/encounters.csv").head(100)[INPUTS].to_dict("records")


def timed(loop, app, sent):
    """The seconds each request took, sent in process one after another, as (path, body)."""

    async def run():
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            times = []
            for path, body in sent:
                started = time.perf_counter()
                response = await client.post(path, json=body)
                times.append(time.perf_counter() - started)
                assert response.status_code == 200
            return times

    return loop.run_until_complete(run())


@pytest.mark.id("tst_1vm3qe")
def test_one_stay(loop, service, requests, record_property):
    """Answers a stay within 100 ms"""
    times = timed(loop, service[0].app, [("/predict", stay) for stay in requests[:20]])
    median = statistics.median(times)
    record_property("note", f"Median {median * 1000:.0f} ms over {len(times)} requests")
    assert median < 0.1


@pytest.mark.id("tst_38831z")
def test_a_batch(loop, service, requests, record_property):
    """Answers 100 stays within 250 ms"""
    times = timed(loop, service[0].app, [("/predict/batch", {"stays": requests})] * 5)
    median = statistics.median(times)
    record_property("note", f"Median {median * 1000:.0f} ms over {len(times)} batches")
    assert median < 0.25


@pytest.mark.id("tst_z4r1l1")
def test_other_versions(service):
    """Won't start on a model trained with other versions"""
    trained = service[1]
    running = train.versions()
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(train, "versions", lambda: {**running, "scikit-learn": "1.0.0"})
        train.save(trained)
    sys.modules.pop("app", None)
    try:
        with pytest.raises(ValueError):
            importlib.import_module("app")
    finally:
        train.save(trained)
        sys.modules.pop("app", None)
