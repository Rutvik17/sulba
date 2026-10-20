import csv

import numpy as np
import pytest

from index import INDEX, build, search, uses_index
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


def questions(count):
    """The first count validation questions' vectors."""
    with open("data/questions.csv", encoding="utf-8", newline="") as file:
        validation = [
            row["question"]
            for row in csv.DictReader(file)
            if row["set"] == "validation"
        ]
    with open("data/question-vectors.csv", encoding="utf-8", newline="") as file:
        rows = {row[0]: row[1:] for row in list(csv.reader(file))[1:]}
    return [np.array(rows[id_], dtype=np.float32) / 32767 for id_ in validation[:count]]


@pytest.fixture(scope="module")
def rows():
    return passages()


def exact(rows, question, k=10):
    """The ids of the k passages nearest to question, worked out over every row."""
    matrix = np.array([row[4] for row in rows], dtype=np.float64)
    cosines = (
        matrix @ question / np.linalg.norm(matrix, axis=1) / np.linalg.norm(question)
    )
    return [rows[i][0] for i in np.argsort(-cosines, kind="stable")[:k]]


def overlap(conn, rows, asked, ef_search):
    """The share of the exact top 10 the index's search finds, over the questions."""
    found = [search(conn, question, 10, ef_search) for question in asked]
    return np.mean(
        [
            len(set(f) & set(exact(rows, q))) / 10
            for f, q in zip(found, asked, strict=True)
        ]
    )


def scans(conn):
    """How many times the index has been scanned, counting this connection's own scans."""
    conn.execute("SELECT pg_stat_force_next_flush()")
    conn.execute("SELECT 1")
    return conn.execute(
        "SELECT idx_scan FROM pg_stat_user_indexes WHERE indexrelname = %s", (INDEX,)
    ).fetchone()[0]


@pytest.mark.id("tst_ewt7ub")
def test_index(database, rows):
    """An HNSW index for cosine distance, with the options given"""
    with connect(database) as conn:
        create(conn)
        load(conn, rows)
        build(conn, m=12, ef_construction=48)
        definition = conn.execute(
            "SELECT indexdef FROM pg_indexes WHERE indexname = %s", (INDEX,)
        ).fetchone()[0]
    assert "USING hnsw (embedding vector_cosine_ops)" in definition
    assert "m='12'" in definition
    assert "ef_construction='48'" in definition


@pytest.mark.id("tst_k7thgg")
def test_plan(database, rows):
    """The plan goes through the index once it's built"""
    question = questions(1)[0]
    with connect(database) as conn:
        create(conn)
        load(conn, rows)
        before = uses_index(conn, question)
        build(conn)
        after = uses_index(conn, question)
    assert (before, after) == (False, True)


@pytest.mark.id("tst_bhbw7y")
def test_search(database, rows):
    """Nearly every passage the exact search finds, through the index"""
    asked = questions(50)
    with connect(database) as conn:
        create(conn)
        load(conn, rows)
        build(conn)
        before = scans(conn)
        assert overlap(conn, rows, asked, 40) >= 0.95
        assert scans(conn) - before >= len(asked)


@pytest.mark.id("tst_9ks2xj")
def test_ef_search(database, rows):
    """A longer candidate list finds more, for its search alone"""
    asked = questions(50)
    with connect(database) as conn:
        create(conn)
        load(conn, rows)
        build(conn, m=4, ef_construction=8)
        short, long = overlap(conn, rows, asked, 10), overlap(conn, rows, asked, 200)
        setting = conn.execute("SHOW hnsw.ef_search").fetchone()[0]
    assert long > short
    assert setting == "40"
