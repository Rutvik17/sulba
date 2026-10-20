import csv

import numpy as np
import pytest

from index import INDEX, build
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


def questions():
    """Every tenth validation question's vector."""
    with open("data/questions.csv", encoding="utf-8", newline="") as file:
        validation = [
            row["question"]
            for row in csv.DictReader(file)
            if row["set"] == "validation"
        ]
    with open("data/question-vectors.csv", encoding="utf-8", newline="") as file:
        rows = {row[0]: row[1:] for row in list(csv.reader(file))[1:]}
    return [np.array(rows[id_], dtype=np.float32) / 32767 for id_ in validation[::10]]


@pytest.fixture(scope="module")
def rows():
    return passages()


@pytest.fixture(scope="module")
def asked():
    return questions()


def ready(database, rows):
    """A connection to the database, with the passages and their index."""
    conn = connect(database)
    create(conn)
    load(conn, rows)
    build(conn)
    return conn


def units(rows):
    matrix = np.array([row[4] for row in rows], dtype=np.float64)
    return matrix / np.linalg.norm(matrix, axis=1, keepdims=True)


def scans(conn):
    """How many times the index has been scanned, counting this connection's own scans."""
    conn.execute("SELECT pg_stat_force_next_flush()")
    conn.execute("SELECT 1")
    return conn.execute(
        "SELECT idx_scan FROM pg_stat_user_indexes WHERE indexrelname = %s", (INDEX,)
    ).fetchone()[0]


@pytest.mark.id("tst_0bfibb")
def test_index(database, rows, asked):
    """Every search goes through the index"""
    with ready(database, rows) as conn:
        before = scans(conn)
        for question in asked[:20]:
            search(conn, question)
        after = scans(conn)
    assert after - before >= 20


@pytest.mark.id("tst_r6s1ca")
def test_names(database, rows, asked):
    """A service's name stays a name"""
    with ready(database, rows) as conn:
        assert search_in(conn, asked[0], "va' OR 'x' = 'x") == []
        assert search_in(conn, asked[0], "veterans' affairs") == []


@pytest.mark.id("tst_5i617b")
def test_order(database, rows, asked):
    """Each service's passages, nearest first"""
    ids = [row[0] for row in rows]
    matrix = units(rows)
    with ready(database, rows) as conn:
        for question in asked:
            distances = dict(zip(ids, 1 - matrix @ question / np.linalg.norm(question)))
            for domain in sorted({row[1] for row in rows}):
                found = [distances[id_] for id_ in search_in(conn, question, domain)]
                # Two passages a near tie apart may come in either order.
                assert all(b >= a - 1e-6 for a, b in zip(found, found[1:]))


@pytest.mark.id("tst_5nmb9z")
def test_similar(database, rows):
    """The passages most like a passage, most alike first"""
    ids = [row[0] for row in rows]
    matrix = units(rows)
    overlaps = []
    with ready(database, rows) as conn:
        for place in range(0, len(rows), 120):
            cosines = dict(zip(ids, matrix @ matrix[place]))
            del cosines[ids[place]]
            exact = sorted(cosines, key=cosines.get, reverse=True)[:5]
            found = similar(conn, ids[place])
            overlaps.append(len(set(found) & set(exact)) / 5)
            alike = [cosines[id_] for id_ in found]
            assert all(b <= a + 1e-6 for a, b in zip(alike, alike[1:]))
    assert np.mean(overlaps) >= 0.8
