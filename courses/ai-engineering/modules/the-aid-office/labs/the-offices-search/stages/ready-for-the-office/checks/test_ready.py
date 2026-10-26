import csv

import numpy as np
import pytest
from index import DOCUMENT, connect, create, read, sync
from office import EMBEDDER, QUERY, find
from search import search

SCALE = 32767
# The share of the office's test questions whose page find must find, and of the other
# services' test questions it must find no pages for.
FOUND, DECLINED = 0.75, 0.8
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


def asked(model, recorded, path, kept):
    """The questions of the set kept in the file at path, their vectors scripted."""
    found = [row for row in rows(path) if row["set"] == kept]
    model.embeds({QUERY + row["text"]: recorded[1][row["question"]] for row in found})
    return found


@pytest.mark.id("tst_k13407")
def test_found(conn, model, recorded):
    """Finds the page for the office's test questions"""
    questions = asked(model, recorded, "data/questions.csv", "test")
    client = model.client()
    found = sum(
        row["page"] in [page for page, _ in find(conn, client, row["text"])]
        for row in questions
    )
    assert found / len(questions) >= FOUND


@pytest.mark.id("tst_pg5cco")
def test_declined(conn, model, recorded):
    """Declines the other services' test questions"""
    questions = asked(model, recorded, "data/other-questions.csv", "test")
    client = model.client()
    declined = sum(find(conn, client, row["text"]) == [] for row in questions)
    assert declined / len(questions) >= DECLINED


@pytest.mark.id("tst_1y9bm9")
def test_model_down(conn, model):
    """By its words when the model fails, drops the connection or never answers"""
    model.fails(503, "Loading model")
    model.disconnects()
    model.hangs()
    client = model.client(timeout=None)
    expected = search(conn, None, QUESTION, 0)
    assert expected
    for _ in range(3):
        assert find(conn, client, QUESTION) == expected


@pytest.mark.id("tst_2sqol0")
def test_one_request(conn, model, recorded):
    """Embeds each question once, as a query"""
    questions = asked(model, recorded, "data/questions.csv", "validation")[:20]
    client = model.client()
    for row in questions:
        before = len(model.requests)
        find(conn, client, row["text"])
        [request] = model.requests[before:]
        assert request.body["model"] == EMBEDDER
        assert request.body["input"] == [QUERY + row["text"]]


@pytest.mark.id("tst_vkwkrh")
def test_pages(conn, model, recorded):
    """Five pages at most, each once, with a passage of its own"""
    pages_of = dict(conn.execute("SELECT id, page FROM passages").fetchall())
    questions = asked(model, recorded, "data/questions.csv", "validation")
    client = model.client()
    for row in questions:
        found = find(conn, client, row["text"])
        assert len(found) <= 5
        assert len({page for page, _ in found}) == len(found)
        assert all(pages_of[id_] == page for page, id_ in found)
