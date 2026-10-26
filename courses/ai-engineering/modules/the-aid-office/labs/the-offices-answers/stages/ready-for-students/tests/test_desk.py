import csv

import numpy as np
import pytest
from desk import Reply, create_tickets, respond
from records import lines, record
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
        create_tickets(conn)
        yield conn


def chats(model):
    return [
        request for request in model.requests if request.path == "/v1/chat/completions"
    ]


def tickets(conn):
    return conn.execute("SELECT student, question FROM tickets ORDER BY id").fetchall()


@pytest.mark.id("tst_y50o1e")
def test_my_aid(conn, model):
    """Gives a signed-in student their own aid"""
    reply = respond(conn, model.client(), "S1002", "What's my aid?", "my aid")
    assert reply == Reply("\n".join(lines(record(conn, "S1002"))), [], False)
    assert chats(model) == []


@pytest.mark.id("tst_vejtab")
def test_pages(conn, model, asked):
    """Answers a question from the office's pages"""
    model.says("Renew it each year on fafsa.gov [1].")
    reply = respond(conn, model.client(), "S1002", asked["q1"])
    assert reply.text == "Renew it each year on fafsa.gov [1]."
    assert len(reply.pages) == 1 and not reply.to_staff
