import csv

import numpy as np
import pytest
from answers import INSTRUCTIONS, MAX_TOKENS, MODEL, STAFF, Answer, answer, cited
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


@pytest.fixture(scope="module")
def asked():
    """The office's questions and the other services', by id."""
    found = rows("data/questions.csv") + rows("data/other-questions.csv")
    return {row["question"]: row["text"] for row in found}


@pytest.fixture
def conn(database, model, recorded, asked):
    passages = read("data/passages.csv")
    model.embeds(
        {
            **{DOCUMENT + p.text: recorded[0][p.id] for p in passages},
            **{QUERY + text: recorded[1][name] for name, text in asked.items()},
        }
    )
    with connect(database) as conn:
        create(conn)
        sync(conn, model.client(), passages)
        yield conn


def chats(model):
    return [
        request for request in model.requests if request.path == "/v1/chat/completions"
    ]


@pytest.mark.id("tst_l8gtvz")
def test_cited():
    """Reads the pages cited, in the order first cited, each once"""
    pages = ["a", "b", "c", "b"]
    assert cited("See [2], then [1] and [2] again, and [4].", pages) == ["b", "a"]
    assert cited("See [5] and [0].", pages) == []
    assert cited("I don't know.", pages) == []


@pytest.mark.id("tst_uy113v")
def test_request(conn, model, asked):
    """Asks the model once, with the passages found, numbered, then the question"""
    model.says("Renew it on fafsa.gov [1].")
    answer(conn, model.client(), asked["q1"])
    [request] = chats(model)
    assert request.body["model"] == MODEL
    assert request.body["max_tokens"] == MAX_TOKENS
    system, user = request.body["messages"]
    assert system == {"role": "system", "content": INSTRUCTIONS}
    bodies = dict(conn.execute("SELECT id, body FROM passages").fetchall())
    place = 0
    for number, (_, id_) in enumerate(find(conn, model.client(), asked["q1"]), start=1):
        place = user["content"].index(f"[{number}]", place)
        place = user["content"].index(bodies[id_], place)
    assert user["content"].endswith(asked["q1"])


@pytest.mark.id("tst_37wkj0")
def test_answer(conn, model, asked):
    """Gives the reply with the pages it cites"""
    found = find(conn, model.client(), asked["q1"])
    model.says("Renew it [2], each year [1].")
    pages = list(dict.fromkeys([found[1][0], found[0][0]]))
    expected = Answer("Renew it [2], each year [1].", pages, False)
    assert answer(conn, model.client(), asked["q1"]) == expected


@pytest.mark.id("tst_xielaq")
def test_declined(conn, model, asked):
    """Passes another service's question to staff without asking the model"""
    assert answer(conn, model.client(), asked["o2"]) == Answer(STAFF, [], True)
    assert chats(model) == []


@pytest.mark.id("tst_5dtxwo")
def test_to_staff(conn, model, asked):
    """Passes the question to staff when the model doesn't know, cites nothing or fails"""
    client = model.client(timeout=None)
    for reply in (
        "I don't know.",
        "You can renew it online.",
        "Renew it [1]. I don't know when.",
    ):
        model.says(reply)
        assert answer(conn, client, asked["q1"]) == Answer(STAFF, [], True)
    for fail in (
        lambda: model.fails(503, "Loading model"),
        model.disconnects,
        model.hangs,
    ):
        model.answers(lambda received, fail=fail: fail())
        assert answer(conn, client, asked["q1"]) == Answer(STAFF, [], True)
