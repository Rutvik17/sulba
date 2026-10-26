import csv

import numpy as np
import pytest
from finder import QUERY, find, pages
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


@pytest.fixture(scope="module")
def validation():
    return [row for row in rows("data/questions.csv") if row["set"] == "validation"]


@pytest.fixture
def conn(database, model, recorded):
    passages = read("data/passages.csv")
    model.embeds({DOCUMENT + p.text: recorded[0][p.id] for p in passages})
    with connect(database) as conn:
        create(conn)
        sync(conn, model.client(), passages)
        yield conn


@pytest.mark.id("tst_8obe4t")
def test_words(conn, model, validation):
    """By any of a question's words when the model is down"""
    found = 0
    for row in validation:
        model.fails(503, "Loading model")
        found += bool(find(conn, model.client(), row["text"]))
    assert found / len(validation) >= 0.95


@pytest.mark.id("tst_a57n7i")
def test_best_first(conn, recorded, validation):
    """The best pages, best first"""
    pages_of = dict(conn.execute("SELECT id, page FROM passages").fetchall())
    query = (
        "SELECT id, embedding <=> %s FROM passages ORDER BY embedding <=> %s LIMIT 40"
    )
    for row in validation[:20]:
        vector = recorded[1][row["question"]]
        nearest = conn.execute(query, (vector, vector)).fetchall()
        expected = []
        for id_, _ in sorted(nearest, key=lambda found: (found[1], found[0])):
            if pages_of[id_] not in [page for page, _ in expected]:
                expected.append((pages_of[id_], id_))
        # A question none of whose words any passage holds, so its pages come by
        # meaning alone.
        assert pages(conn, vector, "Qwxz vbnm") == expected[:5]


@pytest.mark.id("tst_lkc5yv")
def test_keeps(conn, model, recorded, validation):
    """Pages for the office's own questions"""
    model.embeds(
        {QUERY + row["text"]: recorded[1][row["question"]] for row in validation}
    )
    found = sum(bool(find(conn, model.client(), row["text"])) for row in validation)
    assert found / len(validation) >= 0.9


@pytest.mark.id("tst_p75a0o")
def test_other_errors(conn, model):
    """By its words when the model drops the connection or never answers"""
    model.disconnects()
    model.hangs()
    client = model.client()
    for _ in range(2):
        assert find(conn, client, QUESTION)
