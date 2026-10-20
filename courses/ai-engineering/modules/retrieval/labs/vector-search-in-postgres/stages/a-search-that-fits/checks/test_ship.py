import csv

import numpy as np
import pytest

from desk import build, search, update
from store import connect, create, load

# The bytes the table's indexes may take, besides its primary key, how many passages a
# question gets, and the share of the full vectors' nearest the search must find.
BUDGET = 2 * 1024 * 1024
K = 10
KEPT = 0.95


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
    """The test questions' vectors."""
    with open("data/questions.csv", encoding="utf-8", newline="") as file:
        test = [row["question"] for row in csv.DictReader(file) if row["set"] == "test"]
    with open("data/question-vectors.csv", encoding="utf-8", newline="") as file:
        rows = {row[0]: row[1:] for row in list(csv.reader(file))[1:]}
    return [np.array(rows[id_], dtype=np.float32) / 32767 for id_ in test]


@pytest.fixture(scope="module")
def rows():
    return passages()


@pytest.fixture(scope="module")
def asked():
    return questions()


def ready(database, rows):
    """A connection to the database, with the passages and the search's indexes."""
    conn = connect(database)
    create(conn)
    load(conn, rows)
    build(conn)
    return conn


def distances(rows, question):
    """Each passage's cosine distance to question, by the full vectors, by its id."""
    matrix = np.array([row[4] for row in rows], dtype=np.float64)
    cosines = (
        matrix @ question / np.linalg.norm(matrix, axis=1) / np.linalg.norm(question)
    )
    return {row[0]: 1 - cosine for row, cosine in zip(rows, cosines, strict=True)}


def nearest(rows, question, domain=None):
    """The ids of the K passages nearest to question by the full vectors."""
    by_id = distances(rows, question)
    ids = [row[0] for row in rows if domain is None or row[1] == domain]
    return sorted(ids, key=by_id.get)[:K]


def indexes(conn, what):
    """A sum over the table's indexes besides its primary key."""
    return conn.execute(
        f"SELECT coalesce(sum({what}), 0) FROM pg_index i "
        "JOIN pg_stat_user_indexes s ON s.indexrelid = i.indexrelid "
        "WHERE i.indrelid = 'passages'::regclass AND NOT i.indisprimary"
    ).fetchone()[0]


def scans(conn):
    """How many times the indexes have been scanned, counting this connection's own."""
    conn.execute("SELECT pg_stat_force_next_flush()")
    conn.execute("SELECT 1")
    return indexes(conn, "s.idx_scan")


@pytest.mark.id("tst_oqsptj")
def test_budget(database, rows):
    """Indexes within the budget"""
    with ready(database, rows) as conn:
        size = indexes(conn, "pg_relation_size(i.indexrelid)")
    assert 0 < size <= BUDGET


@pytest.mark.id("tst_kpbdml")
def test_recall(database, rows, asked):
    """Finds what the full vectors find"""
    with ready(database, rows) as conn:
        found = [search(conn, question, K) for question in asked]
    overlaps = [
        len(set(ids) & set(nearest(rows, question))) / K
        for ids, question in zip(found, asked, strict=True)
    ]
    assert np.mean(overlaps) >= KEPT


@pytest.mark.id("tst_0fwmyo")
def test_services(database, rows, asked):
    """k passages from each service, nearest first"""
    service = {row[0]: row[1] for row in rows}
    with ready(database, rows) as conn:
        for question in asked[::10]:
            by_id = distances(rows, question)
            for domain in sorted(set(service.values())):
                found = search(conn, question, K, domain)
                assert len(found) == K
                assert {service[id_] for id_ in found} == {domain}
                gaps = [by_id[b] - by_id[a] for a, b in zip(found, found[1:])]
                # Two passages a near tie apart may come in either order.
                assert min(gaps) >= -1e-6


@pytest.mark.id("tst_r0d40o")
def test_index(database, rows, asked):
    """Through the index"""
    with ready(database, rows) as conn:
        before = scans(conn)
        for question in asked[:10]:
            search(conn, question, K)
            search(conn, question, K, "ssa")
        after = scans(conn)
    assert after - before >= 20


@pytest.mark.id("tst_6gnd5d")
def test_update(database, rows, asked):
    """Finds a changed passage by what it says now"""
    first = rows[0]
    changed = (first[0], first[1], first[2], "A new text.", asked[0])
    added = ("p-new", "va", "page-new", "A new passage.", asked[1])
    with ready(database, rows) as conn:
        update(conn, [changed, added])
        count, body = conn.execute(
            "SELECT count(*), max(body) FILTER (WHERE id = %s) FROM passages",
            (first[0],),
        ).fetchone()
        assert search(conn, asked[0], 1) == [first[0]]
        assert search(conn, asked[1], 1) == ["p-new"]
        assert search(conn, asked[1], 1, "va") == ["p-new"]
    assert (count, body) == (len(rows) + 1, "A new text.")
