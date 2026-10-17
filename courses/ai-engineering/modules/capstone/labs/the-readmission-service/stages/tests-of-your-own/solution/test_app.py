"""Tests of the readmission service, sent to it in process as the planners' system would."""

import pandas as pd
import pytest
from httpx import ASGITransport, AsyncClient

import app
from features import DEATH_OR_HOSPICE, INPUTS, features
from train import load


def send(loop, method, path, body=None):
    """The service's response to one request, sent in process."""

    async def request():
        transport = ASGITransport(app=app.app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.request(method, path, json=body)

    return loop.run_until_complete(request())


@pytest.fixture(scope="module")
def saved():
    return load()


@pytest.fixture(scope="module")
def requests(saved):
    """The extract's first 200 living stays as requests send them, each with the saved
    model's probability, the most likely to come back first."""
    rows = pd.read_csv(
        "data/encounters.csv", na_values=["?"], keep_default_na=False, nrows=220
    )
    rows = rows[~rows["discharge_disposition_id"].isin(DEATH_OR_HOSPICE)].head(200)
    probabilities = saved["model"].predict_proba(features(rows))[:, 1]
    ranked = rows.assign(probability=probabilities).sort_values(
        "probability", ascending=False
    )
    return list(zip(ranked[INPUTS].to_dict("records"), ranked["probability"]))


def test_health(loop):
    assert send(loop, "GET", "/health").json() == {"status": "ok"}


def test_calls_at_the_threshold(loop, saved, requests):
    # At or above the saved threshold, though under 0.5.
    stay = next(stay for stay, p in requests if saved["threshold"] <= p < 0.5)
    assert send(loop, "POST", "/predict", stay).json()["call"] is True


def test_no_call_below_the_threshold(loop, saved, requests):
    stay, probability = requests[-1]
    assert probability < saved["threshold"]
    assert send(loop, "POST", "/predict", stay).json()["call"] is False


def test_days_out_of_range(loop, requests):
    for days in (0, 15):
        stay = {**requests[0][0], "time_in_hospital": days}
        assert send(loop, "POST", "/predict", stay).status_code == 422, days


def test_deaths_and_hospice_care_refused(loop, requests):
    stay = requests[0][0]
    ended = [{**stay, "discharge_disposition_id": code} for code in DEATH_OR_HOSPICE]
    response = send(loop, "POST", "/predict/batch", {"stays": ended})
    assert response.status_code == 422
    assert len(response.json()["detail"]) == len(ended)


def test_batch_in_order(loop, saved, requests):
    batch = [stay for stay, _ in requests[:10]]
    answers = send(loop, "POST", "/predict/batch", {"stays": batch}).json()
    expected = saved["model"].predict_proba(features(pd.DataFrame(batch)))[:, 1]
    found = [answer["probability"] for answer in answers["predictions"]]
    assert found == pytest.approx(expected.tolist(), abs=1e-12)


def test_full_batch(loop, requests):
    full = [stay for stay, _ in requests[: app.BATCH_LIMIT]]
    assert send(loop, "POST", "/predict/batch", {"stays": full}).status_code == 200
    over = [stay for stay, _ in requests[: app.BATCH_LIMIT + 1]]
    assert send(loop, "POST", "/predict/batch", {"stays": over}).status_code == 422
