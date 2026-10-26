import csv
from collections import defaultdict

import numpy as np
import pytest
from index import DOCUMENT, connect, create, read, sync
from search import CANDIDATES, K, PAGES, hit_rate, reciprocal_rank, search

PASSAGES = "data/passages.csv"
QUESTIONS = "data/questions.csv"
SCALE = 32767
# The share of the validation questions whose page the search must find among its
# pages, and their mean reciprocal rank, for meaning alone and for the two fused.
FOUND, RANKED = 0.8, 0.7
QUESTION = "How do I renew my FAFSA?"


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
def recorded():
    return vectors("data/passage-vectors.csv", "passage"), vectors(
        "data/question-vectors.csv", "question"
    )


@pytest.fixture
def conn(database, model, recorded):
    passages = read(PASSAGES)
    model.embeds({DOCUMENT + p.text: recorded[0][p.id] for p in passages})
    with connect(database) as conn:
        create(conn)
        sync(conn, model.client(), passages)
        yield conn


def meaning(conn, vector):
    """The CANDIDATES passages nearest to vector, through the index, nearest first."""
    query = (
        "SELECT id, embedding <=> %s FROM passages ORDER BY embedding <=> %s LIMIT %s"
    )
    found = conn.execute(query, (vector, vector, CANDIDATES)).fetchall()
    return [id_ for id_, _ in sorted(found, key=lambda row: (row[1], row[0]))]


def matching(conn, question):
    """The CANDIDATES passages whose words best match the question's, best first."""
    query = (
        "SELECT id FROM passages, "
        "CAST(replace(plainto_tsquery('english', %s)::text, '&', '|') AS tsquery) "
        "AS query "
        "WHERE words @@ query ORDER BY ts_rank(words, query) DESC, id LIMIT %s"
    )
    return [row[0] for row in conn.execute(query, (question, CANDIDATES))]


def expected(conn, vector, question, weight):
    """The pages the search should find, each with its best passage."""
    pages = dict(conn.execute("SELECT id, page FROM passages").fetchall())
    scores = defaultdict(float)
    nearest = meaning(conn, vector) if vector is not None else []
    for share, ranking in ((weight, nearest), (1 - weight, matching(conn, question))):
        for rank, id_ in enumerate(ranking, start=1):
            scores[id_] += share / (K + rank)
    found = []
    for id_ in sorted(scores, key=lambda id_: (-scores[id_], id_)):
        if scores[id_] == 0:
            break
        if pages[id_] not in [page for page, _ in found]:
            found.append((pages[id_], id_))
    return found[:PAGES]


@pytest.mark.id("tst_ygt9k7")
def test_meaning(conn, recorded):
    """With a weight of 1, finds the pages of the nearest passages, each once"""
    vector = recorded[1]["q1"]
    assert search(conn, vector, QUESTION, 1) == expected(conn, vector, QUESTION, 1)


@pytest.mark.id("tst_12chxn")
def test_words(conn, recorded):
    """With a weight of 0, finds the pages whose words best match the question's"""
    vector = recorded[1]["q1"]
    assert search(conn, vector, QUESTION, 0) == expected(conn, vector, QUESTION, 0)


@pytest.mark.id("tst_ebj88o")
def test_no_vector(conn):
    """With no vector, finds pages by words alone, and none for a question no
    passage's words match"""
    assert search(conn, None, QUESTION, 0) == expected(conn, None, QUESTION, 0)
    assert search(conn, None, QUESTION, 0)
    assert search(conn, None, "Qwxz vbnm", 0) == []


@pytest.mark.id("tst_rouhsz")
def test_fused(conn, recorded):
    """Fuses the two rankings by their ranks, with each one's weight"""
    for row in rows(QUESTIONS)[:20]:
        vector = recorded[1][row["question"]]
        for weight in (0.5, 0.8):
            found = search(conn, vector, row["text"], weight)
            assert found == expected(conn, vector, row["text"], weight)


@pytest.mark.id("tst_ckaqt3")
def test_pages(conn, recorded):
    """Gives as many pages as asked for"""
    vector = recorded[1]["q1"]
    assert len(search(conn, vector, QUESTION, 0.5, pages=10)) == 10
    assert [page for page, _ in search(conn, vector, QUESTION, 0.5, pages=2)] == [
        page for page, _ in search(conn, vector, QUESTION, 0.5)
    ][:2]


@pytest.mark.id("tst_e6y1j2")
def test_quotes(conn, recorded):
    """Sends the question to Postgres as a parameter, quotes and all"""
    vector = recorded[1]["q1"]
    for question in ("What's an FSA ID?", "x'; DROP TABLE passages; --", "the of and"):
        search(conn, vector, question, 0.5)
    assert conn.execute("SELECT count(*) FROM passages").fetchone()[0] > 0


@pytest.mark.id("tst_mdi8d0")
def test_measures():
    """Gives the hit rate and the mean reciprocal rank of the pages found"""
    found = [["a", "b"], ["c", "d", "e"], ["f"], []]
    answers = ["a", "e", "g", "h"]
    assert hit_rate(found, answers) == 0.5
    assert reciprocal_rank(found, answers) == pytest.approx((1 + 1 / 3) / 4)


@pytest.mark.id("tst_mkbq8b")
def test_validation(conn, recorded):
    """Finds the page of most of the validation questions, by meaning alone and fused"""
    questions = [row for row in rows(QUESTIONS) if row["set"] == "validation"]
    answers = [row["page"] for row in questions]
    for weight in (1, 0.8):
        found = [
            [
                page
                for page, _ in search(
                    conn, recorded[1][row["question"]], row["text"], weight
                )
            ]
            for row in questions
        ]
        assert hit_rate(found, answers) >= FOUND
        assert reciprocal_rank(found, answers) >= RANKED
