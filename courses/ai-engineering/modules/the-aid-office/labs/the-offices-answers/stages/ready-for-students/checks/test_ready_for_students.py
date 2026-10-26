import csv

import numpy as np
import pytest
from answers import STAFF
from desk import NO_RECORD, SIGN_IN, STAFF_SIGNED_OUT, Reply, create_tickets, respond
from records import lines, record
from index import DOCUMENT, connect, create, read, sync
from office import QUERY
from office_records import STUDENTS
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
        create_tickets(conn)
        yield conn


def chats(model):
    return [
        request for request in model.requests if request.path == "/v1/chat/completions"
    ]


def tickets(conn):
    return conn.execute("SELECT student, question FROM tickets ORDER BY id").fetchall()


@pytest.mark.id("tst_15l6jj")
def test_own_aid(conn, model):
    """Each student's own aid, and nobody else's"""
    students = [student for student, _ in STUDENTS]
    for student in students:
        reply = respond(
            conn, model.client(), student, f"What was {students[0]} offered?", "my aid"
        )
        assert reply.text == "\n".join(lines(record(conn, student)))
    assert respond(conn, model.client(), "S9999", "My aid?", "my aid").text == NO_RECORD
    assert chats(model) == []


@pytest.mark.id("tst_i4bwfk")
def test_signed_out(conn, model, asked):
    """Asks a visitor to sign in for their aid or a reply from staff, and writes no ticket"""
    assert respond(conn, model.client(), None, "My aid?", "my aid") == Reply(
        SIGN_IN, [], False
    )
    assert respond(conn, model.client(), None, asked["o2"]) == Reply(
        STAFF_SIGNED_OUT, [], True
    )
    model.says("Renew it each year on fafsa.gov [1].")
    assert not respond(conn, model.client(), None, asked["q1"]).to_staff
    assert tickets(conn) == []


@pytest.mark.id("tst_mzfd2v")
def test_tickets(conn, model, asked):
    """A ticket for each question that goes to staff, with its student, and none for the rest"""
    model.says("I don't know.")
    model.says("Renew it each year on fafsa.gov [1].")
    respond(conn, model.client(), "S1002", asked["q1"])
    respond(conn, model.client(), "S1003", asked["q1"])
    respond(conn, model.client(), "S1004", asked["o2"])
    assert tickets(conn) == [("S1002", asked["q1"]), ("S1004", asked["o2"])]


@pytest.mark.id("tst_2g2mi9")
def test_model_down(conn, model, asked):
    """Staff answer when the model fails, with a ticket"""
    model.answers(lambda received: model.fails(503, "Loading model"))
    reply = respond(conn, model.client(timeout=None), "S1005", asked["q1"])
    assert reply == Reply(STAFF, [], True)
    assert tickets(conn) == [("S1005", asked["q1"])]


@pytest.mark.id("tst_mjq3u9")
def test_one_request(conn, model, asked):
    """One request to the model for a question from the pages, and none for aid"""
    model.says("Renew it each year on fafsa.gov [1].")
    respond(conn, model.client(), "S1002", asked["q1"])
    respond(conn, model.client(), "S1002", "My aid?", "my aid")
    assert len(chats(model)) == 1
