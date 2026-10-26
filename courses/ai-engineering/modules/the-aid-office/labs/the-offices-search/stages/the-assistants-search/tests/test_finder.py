import csv

import numpy as np
import pytest
from finder import EMBEDDER, QUERY, find
from index import DOCUMENT, connect, create, read, sync

SCALE = 32767
QUESTION = "How do I renew my FAFSA?"


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


@pytest.mark.id("tst_nmwpai")
def test_request(conn, model, recorded):
    """Embeds the question once, as a query"""
    model.embeds({QUERY + QUESTION: recorded[1]["q1"]})
    before = len(model.requests)
    find(conn, model.client(), QUESTION)
    [request] = model.requests[before:]
    assert request.body["model"] == EMBEDDER
    assert request.body["input"] == [QUERY + QUESTION]


@pytest.mark.id("tst_a4bbdv")
def test_declines(conn, model, recorded):
    """Finds no pages for a question about another service"""
    [other] = [
        row for row in rows("data/other-questions.csv") if row["question"] == "o2"
    ]
    model.embeds({QUERY + other["text"]: recorded[1]["o2"]})
    assert find(conn, model.client(), other["text"]) == []


@pytest.mark.id("tst_bo2fu0")
def test_model_error(conn, model):
    """Finds pages by the question's words when the model answers with an error"""
    model.fails(503, "Loading model")
    found = find(conn, model.client(), QUESTION)
    assert 0 < len(found) <= 5
    assert len({page for page, _ in found}) == len(found)
