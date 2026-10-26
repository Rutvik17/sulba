import csv

import numpy as np
import pytest
from answers import INSTRUCTIONS, MAX_TOKENS, MODEL, STAFF, message
from index import DOCUMENT, connect, create, read, sync
from office import QUERY, find
from streamed import Piece, Verdict, stream

SCALE = 32767
TO_STAFF = Verdict(STAFF, [], True)


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
def asked():
    """The office's questions and the other services', by id."""
    found = rows("data/questions.csv") + rows("data/other-questions.csv")
    return {row["question"]: row["text"] for row in found}


@pytest.fixture
def conn(database, model, asked):
    passages = read("data/passages.csv")
    by_passage = vectors("data/passage-vectors.csv", "passage")
    by_question = vectors("data/question-vectors.csv", "question")
    model.embeds(
        {
            **{DOCUMENT + p.text: by_passage[p.id] for p in passages},
            **{QUERY + text: by_question[name] for name, text in asked.items()},
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


@pytest.mark.id("tst_5x6pyh")
def test_pieces(conn, model, asked):
    """Gives each piece as it comes, then the answer with the pages it cites"""
    found = find(conn, model.client(), asked["q1"])
    model.says("Renew it ", "each year ", "on fafsa.gov [2].")
    events = list(stream(conn, model.client(), asked["q1"]))
    assert events == [
        Piece("Renew it "),
        Piece("each year "),
        Piece("on fafsa.gov [2]."),
        Verdict("Renew it each year on fafsa.gov [2].", [found[1][0]], False),
    ]


@pytest.mark.id("tst_7b6r0v")
def test_request(conn, model, asked):
    """Asks for a stream once, with the answer's instructions and message"""
    found = find(conn, model.client(), asked["q1"])
    model.says("Renew it [1].")
    list(stream(conn, model.client(), asked["q1"]))
    [request] = chats(model)
    assert request.body["model"] == MODEL
    assert request.body["stream"] is True
    assert request.body["max_tokens"] == MAX_TOKENS
    assert request.body["messages"] == [
        {"role": "system", "content": INSTRUCTIONS},
        {"role": "user", "content": message(conn, asked["q1"], found)},
    ]


@pytest.mark.id("tst_9vo6lh")
def test_declined(conn, model, asked):
    """Passes another service's question to staff without asking the model"""
    assert list(stream(conn, model.client(), asked["o2"])) == [TO_STAFF]
    assert chats(model) == []


@pytest.mark.id("tst_59ogds")
def test_replaced(conn, model, asked):
    """Ends with staff for a reply that says it doesn't know, cites nothing or is cut off"""
    replies = [
        (("Renew it [1]. ", "I don't know when."), "stop"),
        (("Renew it ", "online."), "stop"),
        (("Renew it [1] ", "and then"), "length"),
    ]
    for pieces, finish in replies:
        model.says(*pieces, finish_reason=finish)
        events = list(stream(conn, model.client(), asked["q1"]))
        assert events == [*(Piece(piece) for piece in pieces), TO_STAFF]


@pytest.mark.id("tst_casmrx")
def test_model_down(conn, model, asked):
    """Ends with staff alone when the model fails, drops the connection or never answers"""
    client = model.client(timeout=None)
    for fail in (
        lambda: model.fails(503, "Loading model"),
        model.disconnects,
        model.hangs,
    ):
        model.answers(lambda received, fail=fail: fail())
        assert list(stream(conn, client, asked["q1"])) == [TO_STAFF]
