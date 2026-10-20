import csv

import psycopg
import pytest

from fts import any_word, every_word, index, load

ROWS = [
    ("p1", "Apply for disability benefits online."),
    ("p2", "Disability benefits for veterans and their families."),
    ("p3", "Renew a driver license by mail."),
    ("p4", "Apply to renew your benefits."),
]
# Postgres's own search, on each passage's words worked out apart from the code's column.
EVERY = (
    "SELECT id FROM expected, websearch_to_tsquery('english', %(question)s) AS query "
    "WHERE found @@ query ORDER BY ts_rank_cd(found, query) DESC, id LIMIT %(k)s"
)
ANY = (
    "WITH asked AS (SELECT replace(plainto_tsquery('english', %(question)s)::text, "
    "'&', '|')::tsquery AS query) "
    "SELECT id FROM expected, asked "
    "WHERE found @@ query ORDER BY ts_rank_cd(found, query) DESC, id LIMIT %(k)s"
)


def ready(database, rows):
    """A connection to the database, with the passages loaded and indexed."""
    conn = psycopg.connect(database, autocommit=True)
    load(conn, rows)
    index(conn)
    return conn


@pytest.fixture(scope="module")
def help_desk():
    """The help desk's passages, as ids and texts, and every tenth validation question."""
    with open("data/passages.csv", encoding="utf-8", newline="") as file:
        rows = [(row["passage"], row["text"]) for row in csv.DictReader(file)]
    with open("data/questions.csv", encoding="utf-8", newline="") as file:
        asked = [
            row["text"] for row in csv.DictReader(file) if row["set"] == "validation"
        ]
    return rows, asked[::10]


@pytest.mark.id("tst_cut1fj")
def test_index(database):
    """Each passage's words kept beside it, with a GIN index on them"""
    conn = ready(database, ROWS)
    (kept,) = conn.execute(
        "SELECT attgenerated FROM pg_attribute "
        "WHERE attrelid = 'passages'::regclass AND attname = 'words'"
    ).fetchone()
    assert kept == "s"
    (words,) = conn.execute(
        "SELECT words::text FROM passages WHERE id = 'p1'"
    ).fetchone()
    assert words == "'appli':1 'benefit':4 'disabl':3 'onlin':5"
    methods = conn.execute(
        "SELECT am.amname FROM pg_index i JOIN pg_class c ON c.oid = i.indexrelid "
        "JOIN pg_am am ON am.oid = c.relam WHERE i.indrelid = 'passages'::regclass"
    ).fetchall()
    assert ("gin",) in methods


@pytest.mark.id("tst_03gc7n")
def test_every_word(database):
    """The passages that hold every word of a question, best first"""
    conn = ready(database, ROWS)
    assert every_word(conn, "disability benefits") == ["p1", "p2"]
    assert every_word(conn, "apply for benefits online") == ["p1"]
    assert every_word(conn, "What is it?") == []


@pytest.mark.id("tst_u4w4ui")
def test_any_word(database):
    """The passages that hold any word of a question, best first"""
    conn = ready(database, ROWS)
    assert any_word(conn, "apply for benefits online", 4) == ["p1", "p4", "p2"]
    assert any_word(conn, "renew benefits", 2) == ["p4", "p1"]
    assert any_word(conn, "What is it?") == []


@pytest.mark.id("tst_zkyr6l")
def test_help_desk(database, help_desk):
    """Every tenth validation question, on the help desk's passages"""
    rows, asked = help_desk
    conn = ready(database, rows)
    conn.execute(
        "CREATE TEMPORARY TABLE expected AS "
        "SELECT id, to_tsvector('english', body) AS found FROM passages"
    )
    for question in asked:
        for search, query in ((every_word, EVERY), (any_word, ANY)):
            found = conn.execute(query, {"question": question, "k": 5}).fetchall()
            assert search(conn, question, 5) == [id_ for (id_,) in found], question
