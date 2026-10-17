import csv
import importlib
import sys

import pandas as pd
import pytest
from httpx import ASGITransport, AsyncClient

from call_list import call_list
from features import features
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


@pytest.fixture(scope="module")
def encounters():
    """The extract's header, and each encounter's line with its fields."""
    with open("data/encounters.csv", newline="") as extract:
        lines = extract.read().splitlines(keepends=True)
    return lines[0], list(zip(lines[1:], csv.DictReader(lines), strict=True))


def day(tmp_path, header, lines):
    """A day's discharges file of these lines of the extract."""
    path = tmp_path / "discharges.csv"
    path.write_text(header + "".join(lines))
    return path


def with_result(row):
    return row["A1Cresult"] != "None"


def living(row):
    return row["discharge_disposition_id"] not in DEATH_OR_HOSPICE


def listed(loop, service, path):
    async def run():
        transport = ASGITransport(app=service[0].app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            return await call_list(client, path)

    return loop.run_until_complete(run())


def expected(service, path):
    """Each living stay of the day's file, with its probability from the saved model."""
    rows = pd.read_csv(path, na_values=["?"], keep_default_na=False)
    rows = rows[~rows["discharge_disposition_id"].astype(str).isin(DEATH_OR_HOSPICE)]
    probabilities = service[1]["model"].predict_proba(features(rows))[:, 1]
    return dict(zip(rows["encounter_id"], probabilities, strict=True))


def assert_listed(found, wanted):
    assert sorted(found["encounter_id"]) == sorted(wanted)
    for encounter, probability in zip(found["encounter_id"], found["probability"]):
        assert probability == pytest.approx(wanted[encounter], abs=1e-12)


@pytest.mark.id("tst_y8w4om")
def test_untested(loop, service, encounters, tmp_path):
    """Lists a day of stays with no HbA1c test"""
    header, all_lines = encounters
    lines = [line for line, row in all_lines if not with_result(row) and living(row)][
        :50
    ]
    path = day(tmp_path, header, lines)
    assert_listed(listed(loop, service, path), expected(service, path))


@pytest.mark.id("tst_47gw7x")
def test_many_batches(loop, service, encounters, tmp_path):
    """Lists every stay of a day of more than one batch"""
    header, all_lines = encounters
    lines = [line for line, row in all_lines if with_result(row) and living(row)][:250]
    path = day(tmp_path, header, lines)
    assert_listed(listed(loop, service, path), expected(service, path))


@pytest.mark.id("tst_031x45")
def test_deaths_left_out(loop, service, encounters, tmp_path):
    """Lists a day with deaths and hospice care, leaving them out"""
    header, all_lines = encounters
    stays = [line for line, row in all_lines if with_result(row) and living(row)][:50]
    ended = [line for line, row in all_lines if with_result(row) and not living(row)][
        :3
    ]
    path = day(tmp_path, header, [*stays[:20], *ended, *stays[20:]])
    found = listed(loop, service, path)
    assert len(found) == len(stays)
    assert_listed(found, expected(service, path))
