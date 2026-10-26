import csv

import numpy as np
import pytest
from desk_answers import STAFF, office_answer, student_record
from office import find
from index import DOCUMENT, connect, create, read, sync
from office import QUERY
from records import create as create_records
from records import load

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
        create_records(conn)
        load(conn)
        yield conn


def chats(model):
    return [
        request for request in model.requests if request.path == "/v1/chat/completions"
    ]


@pytest.mark.id("tst_uosvtq")
def test_declined(conn, model, asked):
    """Another service's question goes to staff, unasked"""
    assert office_answer(conn, model.client(), asked["o2"]) == (STAFF, [])
    assert chats(model) == []


@pytest.mark.id("tst_9b4h1l")
def test_numbers(conn, model, asked):
    """Each number names its own passage's page"""
    found = find(conn, model.client(), asked["q1"])
    model.says("See [1], [3] and [5].")
    _, pages = office_answer(conn, model.client(), asked["q1"])
    assert pages == list(dict.fromkeys([found[0][0], found[2][0], found[4][0]]))


@pytest.mark.id("tst_yv413s")
def test_quotes(conn):
    """A student id stays an id"""
    assert (
        student_record(conn, "S9999', true); RESET ROLE; SELECT set_config('app.x', 'y")
        is None
    )
    assert student_record(conn, "S9999") is None


@pytest.mark.id("tst_q820th")
def test_after_a_record(conn, model, asked):
    """The search still works after a record is read"""
    student_record(conn, "S1002")
    assert find(conn, model.client(), asked["q1"])
