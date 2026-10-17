import csv
import importlib
import sys

import pytest
from httpx import ASGITransport, AsyncClient

from call_list import call_list
from train import save, train

DEATH_OR_HOSPICE = {"11", "13", "14", "19", "20", "21"}


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


@pytest.fixture
def listed(loop, service, tmp_path):
    """The call list for a day of 30 discharges, each with an HbA1c result."""
    with open("data/encounters.csv", newline="") as extract:
        lines = extract.read().splitlines(keepends=True)
    rows = csv.DictReader(lines)
    kept = [
        line
        for line, row in zip(lines[1:], rows, strict=True)
        if row["A1Cresult"] != "None"
        and row["discharge_disposition_id"] not in DEATH_OR_HOSPICE
    ][:30]
    path = tmp_path / "discharges.csv"
    path.write_text(lines[0] + "".join(kept))

    async def run():
        transport = ASGITransport(app=service[0].app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            return await call_list(client, path)

    return loop.run_until_complete(run())


@pytest.mark.id("tst_44i6w7")
def test_columns(listed):
    """Gives each stay's encounter, probability and call"""
    assert list(listed.columns) == ["encounter_id", "probability", "call"]
    assert len(listed) == 30


@pytest.mark.id("tst_827a26")
def test_most_likely_first(listed):
    """Puts the stays most likely to come back first"""
    assert listed["probability"].is_monotonic_decreasing


@pytest.mark.id("tst_sfb75w")
def test_calls(listed, service):
    """Calls the stays at or above the saved threshold"""
    threshold = service[1]["threshold"]
    assert listed["call"].tolist() == (listed["probability"] >= threshold).tolist()
