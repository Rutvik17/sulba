import csv

import numpy as np
import pytest
from desk_answers import STAFF, office_answer, student_record
from index import DOCUMENT, connect, create, read, sync
from office import QUERY
from office_records import AWARDS
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


@pytest.mark.id("tst_22muvo")
def test_record(conn):
    """Reads a student's own record"""
    found = student_record(conn, "S1002")
    assert found.student == "S1002"
    awards = [row for row in AWARDS if row[0] == "S1002"]
    assert len(found.awards) == len(awards)


@pytest.mark.id("tst_nfv6ce")
def test_answer(conn, model, asked):
    """Answers from the office's pages, with a page it cites"""
    model.says("Renew it each year on fafsa.gov [1].")
    text, pages = office_answer(conn, model.client(), asked["q1"])
    assert text == "Renew it each year on fafsa.gov [1]."
    assert len(pages) == 1


@pytest.mark.id("tst_gltvuu")
def test_staff(conn, model, asked):
    """Passes a question to staff when the model can't answer"""
    model.says("I don't know.")
    assert office_answer(conn, model.client(), asked["q1"]) == (STAFF, [])
