import csv

import numpy as np
import pytest

from index import build
from queries import search, search_in, similar
from store import connect, create, load


def passages():
    """The help desk's passages, each its id, domain, page, text and vector."""
    with open("data/passage-vectors.csv", encoding="utf-8", newline="") as file:
        rows = list(csv.reader(file))[1:]
    vectors = {row[0]: np.array(row[1:], dtype=np.float32) / 32767 for row in rows}
    with open("data/passages.csv", encoding="utf-8", newline="") as file:
        return [
            (
                row["passage"],
                row["domain"],
                row["page"],
                row["text"],
                vectors[row["passage"]],
            )
            for row in csv.DictReader(file)
        ]


def question():
    """The first validation question's vector."""
    with open("data/questions.csv", encoding="utf-8", newline="") as file:
        first = next(
            row["question"]
            for row in csv.DictReader(file)
            if row["set"] == "validation"
        )
    with open("data/question-vectors.csv", encoding="utf-8", newline="") as file:
        rows = {row[0]: row[1:] for row in list(csv.reader(file))[1:]}
    return np.array(rows[first], dtype=np.float32) / 32767


@pytest.fixture(scope="module")
def rows():
    return passages()


def ready(database, rows):
    """A connection to the database, with the passages and their index."""
    conn = connect(database)
    create(conn)
    load(conn, rows)
    build(conn)
    return conn


@pytest.mark.id("tst_w0ytu2")
def test_search(database, rows):
    """The nearest passages, each with its similarity, most alike first"""
    with ready(database, rows) as conn:
        found = search(conn, question(), 5)
    similarities = [similarity for _, similarity in found]
    assert len(found) == 5
    assert similarities == sorted(similarities, reverse=True)


@pytest.mark.id("tst_1rk2x4")
def test_search_in(database, rows):
    """Only the service's passages"""
    service = {row[0]: row[1] for row in rows}
    with ready(database, rows) as conn:
        found = search_in(conn, question(), "va")
    assert len(found) == 10
    assert {service[id_] for id_ in found} == {"va"}


@pytest.mark.id("tst_e9nxng")
def test_similar(database, rows):
    """Five passages like a passage, without it"""
    with ready(database, rows) as conn:
        found = similar(conn, rows[0][0])
    assert len(found) == 5
    assert rows[0][0] not in found
