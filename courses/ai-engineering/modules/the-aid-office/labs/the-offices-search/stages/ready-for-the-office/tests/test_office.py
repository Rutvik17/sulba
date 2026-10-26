import csv

import numpy as np
import pytest
from index import DOCUMENT, connect, create, read, sync
from office import QUERY, find

SCALE = 32767


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
    passages = read("data/passages.csv")
    model.embeds({DOCUMENT + p.text: recorded[0][p.id] for p in passages})
    with connect(database) as conn:
        create(conn)
        sync(conn, model.client(), passages)
        yield conn


@pytest.mark.id("tst_zj2zo6")
def test_finds(conn, model, recorded):
    """Finds pages for one of the office's questions"""
    [question] = [row for row in rows("data/questions.csv") if row["question"] == "q1"]
    model.embeds({QUERY + question["text"]: recorded[1]["q1"]})
    found = find(conn, model.client(), question["text"])
    assert 0 < len(found) <= 5


@pytest.mark.id("tst_6xlomt")
def test_declines(conn, model, recorded):
    """Finds no pages for a question about another service"""
    [other] = [
        row for row in rows("data/other-questions.csv") if row["question"] == "o2"
    ]
    model.embeds({QUERY + other["text"]: recorded[1]["o2"]})
    assert find(conn, model.client(), other["text"]) == []
