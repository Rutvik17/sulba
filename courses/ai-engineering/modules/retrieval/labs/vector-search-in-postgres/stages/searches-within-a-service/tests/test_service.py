import csv

import numpy as np
import pytest

from index import INDEX, build
from service import by_service, search_in
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
    """Every tenth validation question's vector and service."""
    with open("data/questions.csv", encoding="utf-8", newline="") as file:
        validation = [row for row in csv.DictReader(file) if row["set"] == "validation"]
    with open("data/question-vectors.csv", encoding="utf-8", newline="") as file:
        rows = {row[0]: row[1:] for row in list(csv.reader(file))[1:]}
    return [
        (np.array(rows[row["question"]], dtype=np.float32) / 32767, row["domain"])
        for row in validation[::10]
    ]


@pytest.fixture(scope="module")
def rows():
    return passages()


@pytest.fixture(scope="module")
def asked():
    return questions()


def services(rows):
    return sorted({row[1] for row in rows})


def distances(rows, question):
    """Each passage's cosine distance to question, by its id."""
    matrix = np.array([row[4] for row in rows], dtype=np.float64)
    cosines = (
        matrix @ question / np.linalg.norm(matrix, axis=1) / np.linalg.norm(question)
    )
    return {row[0]: 1 - cosine for row, cosine in zip(rows, cosines, strict=True)}


def exact_in(rows, question, domain, k=10):
    """The ids of the k passages of domain nearest to question, over every row."""
    by_id = distances(rows, question)
    return sorted((row[0] for row in rows if row[1] == domain), key=by_id.get)[:k]


def scans(conn):
    """How many times the index has been scanned, counting this connection's own scans."""
    conn.execute("SELECT pg_stat_force_next_flush()")
    conn.execute("SELECT 1")
    return conn.execute(
        "SELECT idx_scan FROM pg_stat_user_indexes WHERE indexrelname = %s", (INDEX,)
    ).fetchone()[0]


def indexed(database, rows):
    conn = connect(database)
    create(conn)
    load(conn, rows)
    build(conn)
    return conn


@pytest.mark.id("tst_czu31w")
def test_service(database, rows, asked):
    """Only the service's passages"""
    service = {row[0]: row[1] for row in rows}
    with indexed(database, rows) as conn:
        for question, _ in asked[:10]:
            for domain in services(rows):
                found = search_in(conn, question, domain)
                assert {service[id_] for id_ in found} == {domain}


@pytest.mark.id("tst_iqqau8")
def test_count(database, rows, asked):
    """k passages from each service, whichever service the question is about"""
    with indexed(database, rows) as conn:
        for question, _ in asked:
            for domain in services(rows):
                assert len(search_in(conn, question, domain)) == 10
        assert len(search_in(conn, asked[0][0], "va", 3)) == 3


@pytest.mark.id("tst_cc7x2t")
def test_order(database, rows, asked):
    """Nearest first"""
    with indexed(database, rows) as conn:
        for question, _ in asked:
            by_id = distances(rows, question)
            for domain in services(rows):
                found = [by_id[id_] for id_ in search_in(conn, question, domain)]
                # Two passages a near tie apart may come in either order.
                assert all(b >= a - 1e-6 for a, b in zip(found, found[1:]))


@pytest.mark.id("tst_leh49c")
def test_recall(database, rows, asked):
    """Nearly every passage the exact search finds, in the other services too"""
    overlaps = []
    with indexed(database, rows) as conn:
        for question, own in asked:
            for domain in services(rows):
                if domain != own:
                    found = search_in(conn, question, domain)
                    exact = exact_in(rows, question, domain)
                    overlaps.append(len(set(found) & set(exact)) / 10)
    assert np.mean(overlaps) >= 0.9


@pytest.mark.id("tst_kwp047")
def test_index(database, rows, asked):
    """Through the index, with its settings for each search alone"""
    with indexed(database, rows) as conn:
        before = scans(conn)
        for question, _ in asked[:10]:
            search_in(conn, question, "dmv", 10, 20)
        after = scans(conn)
        settings = conn.execute(
            "SELECT current_setting('hnsw.iterative_scan'), "
            "current_setting('hnsw.ef_search')"
        ).fetchone()
    assert after - before >= 10
    assert settings == ("off", "40")


@pytest.mark.id("tst_jxayrn")
def test_by_service(database, rows, asked):
    """The nearest passages in each service, under its name"""
    question = asked[0][0]
    with indexed(database, rows) as conn:
        found = by_service(conn, question, 3)
        each = {
            domain: search_in(conn, question, domain, 3) for domain in services(rows)
        }
    assert found == each
