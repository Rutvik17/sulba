import csv
import math
from dataclasses import replace

import httpx
import numpy as np
import pytest
from index import BATCH, DOCUMENT, EMBEDDER, Passage, connect, create, read, sync

PASSAGES = "data/passages.csv"
VECTORS = "data/passage-vectors.csv"
SCALE = 32767


def rows(path):
    with open(path, encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


@pytest.fixture(scope="module")
def passages():
    return read(PASSAGES)


@pytest.fixture(scope="module")
def vectors(passages):
    """Each passage's text after the document prefix, with its recorded vector."""
    numbers = {
        row["passage"]: [int(row[f"e_{i}"]) / SCALE for i in range(1, 769)]
        for row in rows(VECTORS)
    }
    return {DOCUMENT + p.text: numbers[p.id] for p in passages}


@pytest.fixture
def conn(database):
    with connect(database) as conn:
        create(conn)
        yield conn


def table(conn):
    """Each passage in the table, by id: its page, title, text and vector."""
    found = conn.execute(
        "SELECT id, page, title, body, embedding FROM passages"
    ).fetchall()
    return {
        id_: (page, title, body, vector.to_numpy())
        for id_, page, title, body, vector in found
    }


def embedded(model):
    return [text for request in model.requests for text in request.body["input"]]


@pytest.mark.id("tst_lw2jj8")
def test_read(passages):
    """Reads each passage with its page, title and text, in order"""
    expected = [
        Passage(r["passage"], r["page"], r["title"], r["text"]) for r in rows(PASSAGES)
    ]
    assert passages == expected


@pytest.mark.id("tst_ujth0o")
def test_create(conn):
    """Makes the table, with HNSW and GIN indexes of its vectors and words"""
    columns = dict(
        conn.execute(
            "SELECT column_name, is_nullable FROM information_schema.columns "
            "WHERE table_name = 'passages'"
        ).fetchall()
    )
    for name in ("id", "page", "title", "body", "digest", "embedding"):
        assert columns[name] == "NO"
    indexes = [
        row[0]
        for row in conn.execute(
            "SELECT indexdef FROM pg_indexes WHERE tablename = 'passages'"
        )
    ]
    assert any("USING hnsw (embedding vector_cosine_ops)" in index for index in indexes)
    assert any("USING gin (words)" in index for index in indexes)
    conn.execute(
        "INSERT INTO passages (id, page, title, body, digest, embedding) "
        "VALUES ('x', 'y', 'Loans', 'Repaying them', 'z', %s)",
        (np.ones(768, dtype=np.float32),),
    )
    [words] = conn.execute("SELECT words::text FROM passages").fetchone()
    assert words == "'loan':1 'repay':2"


@pytest.mark.id("tst_9umqup")
def test_sync(conn, model, passages, vectors):
    """Embeds every passage on the first sync, BATCH at a time, and keeps its vector"""
    model.embeds(vectors)
    assert sync(conn, model.client(), passages) == [p.id for p in passages]
    assert embedded(model) == [DOCUMENT + p.text for p in passages]
    assert len(model.requests) == math.ceil(len(passages) / BATCH)
    for request in model.requests:
        assert request.path == "/v1/embeddings"
        assert request.body["model"] == EMBEDDER
        assert len(request.body["input"]) <= BATCH
    found = table(conn)
    assert len(found) == len(passages)
    for p in passages:
        page, title, body, vector = found[p.id]
        assert (page, title, body) == (p.page, p.title, p.text)
        np.testing.assert_allclose(vector, vectors[DOCUMENT + p.text], atol=1e-6)


@pytest.mark.id("tst_z13jrq")
def test_unchanged(conn, model, passages, vectors):
    """Embeds nothing when no passage has changed"""
    model.embeds(vectors)
    sync(conn, model.client(), passages)
    before = len(model.requests)
    assert sync(conn, model.client(), passages) == []
    assert len(model.requests) == before


@pytest.mark.id("tst_npa9l2")
def test_changes(conn, model, passages, vectors):
    """Embeds only new and changed texts, and removes the passages gone"""
    model.embeds(vectors)
    sync(conn, model.client(), passages)
    old = table(conn)
    edited = replace(passages[3], text="Apply by June 30 on fafsa.gov.")
    renamed = replace(passages[5], page="studentaid-1", title="A new title")
    added = Passage("p9999", "studentaid-1", "Deadlines", "The state deadline varies.")
    changed = [*passages[:3], edited, passages[4], renamed, *passages[7:], added]
    model.embeds(
        {
            **vectors,
            DOCUMENT + edited.text: [0.6] * 768,
            DOCUMENT + added.text: [0.8] * 768,
        }
    )
    first = len(model.requests)
    assert sync(conn, model.client(), changed) == [edited.id, added.id]
    assert embedded(model)[len(passages) :] == [
        DOCUMENT + edited.text,
        DOCUMENT + added.text,
    ]
    assert len(model.requests) == first + 1
    found = table(conn)
    assert set(found) == {p.id for p in changed}
    assert found[edited.id][2] == edited.text
    np.testing.assert_allclose(found[edited.id][3], [0.6] * 768, atol=1e-6)
    assert found[added.id][:3] == (added.page, added.title, added.text)
    assert found[renamed.id][:3] == (renamed.page, renamed.title, renamed.text)
    np.testing.assert_allclose(found[renamed.id][3], old[renamed.id][3])


@pytest.mark.id("tst_c7r9hf")
def test_failed_sync(conn, model, passages, vectors):
    """Leaves the table as it was when the model fails"""
    model.embeds(vectors)
    sync(conn, model.client(), passages)
    before = table(conn)
    model.fails(503, "Loading model")
    changed = [replace(passages[0], text="New text."), *passages[2:]]
    with pytest.raises(httpx.HTTPError):
        sync(conn, model.client(), changed)
    after = table(conn)
    assert set(after) == set(before)
    assert after[passages[0].id][2] == passages[0].text
