import csv

import numpy as np
import pytest
from index import DOCUMENT, connect, create, read, sync
from scope import closeness, rates, threshold

PASSAGES = "data/passages.csv"
SCALE = 32767
# The share of the office's validation questions the threshold keeps, and the share of
# the other services' validation questions it must decline.
KEEP, DECLINE = 0.95, 0.75


def rows(path):
    with open(path, encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def vectors(path, name):
    return {
        row[name]: np.array(
            [int(row[f"e_{i}"]) for i in range(1, 769)], dtype=np.float32
        )
        / SCALE
        for row in rows(path)
    }


@pytest.fixture(scope="module")
def recorded():
    return vectors("data/passage-vectors.csv", "passage"), vectors(
        "data/question-vectors.csv", "question"
    )


@pytest.fixture
def conn(database, model, recorded):
    passages = read(PASSAGES)
    model.embeds({DOCUMENT + p.text: recorded[0][p.id] for p in passages})
    with connect(database) as conn:
        create(conn)
        sync(conn, model.client(), passages)
        yield conn


@pytest.mark.id("tst_yonog9")
def test_closeness(conn, recorded):
    """Gives the cosine similarity of the nearest passage"""
    passages = np.array(list(recorded[0].values()), dtype=np.float64)
    passages /= np.linalg.norm(passages, axis=1, keepdims=True)
    for name in ("q1", "q50", "o1", "o200"):
        vector = recorded[1][name].astype(np.float64)
        nearest = np.max(passages @ (vector / np.linalg.norm(vector)))
        assert closeness(conn, recorded[1][name]) == pytest.approx(nearest, abs=1e-5)


@pytest.mark.id("tst_ea6tx3")
def test_threshold():
    """Gives the highest closeness that at least the share asked for reach"""
    similarities = [0.6, 0.9, 0.7, 0.8]
    assert threshold(similarities, 0.5) == 0.8
    assert threshold(similarities, 0.75) == 0.7
    assert threshold(similarities, 1) == 0.6
    assert threshold(similarities, 0.2) == 0.9
    assert threshold([0.1 * n for n in range(10)], 0.7) == pytest.approx(0.3)
    assert threshold([0.5, 0.5, 0.4], 0.5) == 0.5


@pytest.mark.id("tst_yxqrwp")
def test_rates():
    """Gives the share of the office's questions kept and of the others declined"""
    assert rates([0.9, 0.8, 0.6, 0.7], [0.5, 0.7, 0.65], 0.7) == (0.75, 2 / 3)


@pytest.mark.id("tst_ew54g7")
def test_validation(conn, recorded):
    """Keeps most of the office's validation questions and turns away most others"""

    def near(path):
        found = [row for row in rows(path) if row["set"] == "validation"]
        return [closeness(conn, recorded[1][row["question"]]) for row in found]

    office, others = near("data/questions.csv"), near("data/other-questions.csv")
    kept, declined = rates(office, others, threshold(office, KEEP))
    assert kept >= KEEP
    assert declined >= DECLINE
