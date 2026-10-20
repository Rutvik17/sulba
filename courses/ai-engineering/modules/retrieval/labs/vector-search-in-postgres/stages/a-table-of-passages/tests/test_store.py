import csv

import numpy as np
import psycopg
import pytest

from store import connect, create, load, nearest


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


def unit(*values):
    vector = np.zeros(768, dtype=np.float32)
    vector[: len(values)] = values
    return vector / np.linalg.norm(vector)


ROWS = [
    ("p1", "ssa", "page-a", "Apply for benefits online.", unit(1.0, 0.0)),
    ("p2", "va", "page-b", "Renew your license.", unit(0.0, 1.0)),
    ("p3", "dmv", "page-c", "Pay off your loan.", unit(1.0, 1.0)),
]


@pytest.mark.id("tst_us5aen")
def test_columns(database):
    """The table's columns, their types, and its key"""
    with connect(database) as conn:
        create(conn)
        columns = conn.execute(
            "SELECT attname, format_type(atttypid, atttypmod), attnotnull "
            "FROM pg_attribute WHERE attrelid = 'passages'::regclass "
            "AND attnum > 0 AND NOT attisdropped ORDER BY attnum"
        ).fetchall()
        key = conn.execute(
            "SELECT a.attname FROM pg_index i JOIN pg_attribute a "
            "ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey) "
            "WHERE i.indrelid = 'passages'::regclass AND i.indisprimary"
        ).fetchall()
    assert columns == [
        ("id", "text", True),
        ("domain", "text", True),
        ("page", "text", True),
        ("body", "text", True),
        ("embedding", "vector(768)", True),
    ]
    assert key == [("id",)]


@pytest.mark.id("tst_bzq90j")
def test_storage(database):
    """Each vector kept in its row"""
    with connect(database) as conn:
        create(conn)
        storage = conn.execute(
            "SELECT attstorage FROM pg_attribute "
            "WHERE attrelid = 'passages'::regclass AND attname = 'embedding'"
        ).fetchone()[0]
    assert storage == "p"


@pytest.mark.id("tst_k4sto8")
def test_rows(database):
    """Each row as it was loaded, its vector to the last digit"""
    with connect(database) as conn:
        create(conn)
        load(conn, ROWS)
        kept = conn.execute(
            "SELECT id, domain, page, body, embedding FROM passages ORDER BY id"
        ).fetchall()
    assert [row[:4] for row in kept] == [row[:4] for row in ROWS]
    for row, given in zip(kept, ROWS, strict=True):
        assert np.array_equal(row[4].to_numpy(), given[4])


@pytest.mark.id("tst_lhtbl9")
def test_copy(database, monkeypatch):
    """Every passage loaded with one COPY in its binary format"""
    statements = []
    original = psycopg.Cursor.copy

    def copy(cursor, statement, *args, **kwargs):
        if not isinstance(statement, str):
            statement = statement.as_string(cursor.connection)
        statements.append(" ".join(statement.split()).upper())
        return original(cursor, statement, *args, **kwargs)

    monkeypatch.setattr(psycopg.Cursor, "copy", copy)
    rows = passages()
    with connect(database) as conn:
        create(conn)
        load(conn, rows)
        count = conn.execute("SELECT count(*) FROM passages").fetchone()[0]
    assert count == len(rows)
    assert len(statements) == 1
    assert "FORMAT BINARY" in statements[0]


@pytest.mark.id("tst_fk2pxf")
def test_statistics(database):
    """The planner's statistics on the rows, gathered once they're in"""
    rows = passages()
    with connect(database) as conn:
        create(conn)
        load(conn, rows)
        analyzed, counted = conn.execute(
            "SELECT s.analyze_count, c.reltuples FROM pg_stat_user_tables s "
            "JOIN pg_class c ON c.oid = s.relid WHERE s.relname = 'passages'"
        ).fetchone()
    assert analyzed >= 1
    assert counted == len(rows)


@pytest.mark.id("tst_rf3jh2")
def test_nearest(database):
    """The nearest passages by cosine distance, nearest first"""
    rows = passages()
    ids = [row[0] for row in rows]
    matrix = np.array([row[4] for row in rows], dtype=np.float64)
    matrix /= np.linalg.norm(matrix, axis=1, keepdims=True)
    with connect(database) as conn:
        create(conn)
        load(conn, rows)
        for question in questions(20):
            found = nearest(conn, question, 10)
            asked = question / np.linalg.norm(question)
            distances = 1 - matrix @ asked
            got = [distances[ids.index(id_)] for id_ in found]
            # Two passages a near tie apart may come in either order.
            assert np.allclose(got, np.sort(distances)[:10], atol=1e-6)


@pytest.mark.id("tst_tjfk8c")
def test_k(database):
    """k passages, or every passage when there are fewer"""
    with connect(database) as conn:
        create(conn)
        load(conn, ROWS)
        assert nearest(conn, unit(1.0, 0.1), 2) == ["p1", "p3"]
        assert len(nearest(conn, unit(1.0, 0.1), 5)) == 3
