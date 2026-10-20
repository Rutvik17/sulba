import hashlib
import json
import sqlite3

import httpx
import numpy as np
import pytest

from cache import Cache, key
from embed import DOCUMENT, MODEL, QUERY, ModelError

PASSAGES = [
    "You can apply for disability benefits online.",
    "Bring proof of your age to the office.",
    "You can apply for disability benefits online.",
    "Renew your license before it expires.",
]


def vector(text):
    """A short vector of its own for each text."""
    return [len(text) / 100, text.count("e") / 10, 0.5]


def sent(model):
    return [text for request in model.requests for text in request.body["input"]]


@pytest.mark.id("tst_r6v1kc")
def test_key():
    """The sha256 of the model's name, a newline, the prefix and the text"""
    text = PASSAGES[0]
    expected = hashlib.sha256(f"{MODEL}\n{DOCUMENT}{text}".encode()).hexdigest()
    assert key(DOCUMENT, text) == expected
    assert key(QUERY, text) != expected


@pytest.mark.id("tst_x2p7wd")
def test_once(model, tmp_path):
    """Each text embedded once, its vector for each place it has"""
    model.embeds(vector)
    with Cache(tmp_path / "vectors.sqlite") as cache:
        found = cache.vectors(model.client(), PASSAGES, DOCUMENT)
    assert sent(model) == [DOCUMENT + text for text in dict.fromkeys(PASSAGES)]
    assert found.dtype == np.float32
    expected = np.array(
        [vector(DOCUMENT + text) for text in PASSAGES], dtype=np.float32
    )
    assert np.array_equal(found, expected)


@pytest.mark.id("tst_k8n3sy")
def test_kept(model, tmp_path):
    """Vectors kept in the file, and found there again"""
    model.embeds(vector)
    path = tmp_path / "vectors.sqlite"
    with Cache(path) as cache:
        cache.vectors(model.client(), PASSAGES, DOCUMENT)
    first = len(model.requests)
    with Cache(path) as cache:
        again = cache.vectors(model.client(), PASSAGES[::-1], DOCUMENT)
    assert len(model.requests) == first
    expected = np.array(
        [vector(DOCUMENT + text) for text in PASSAGES[::-1]], dtype=np.float32
    )
    assert np.array_equal(again, expected)
    connection = sqlite3.connect(path)
    rows = connection.execute("SELECT key, vector FROM vectors").fetchall()
    connection.close()
    assert len(rows) == 3
    stored = {k: np.frombuffer(blob, dtype=np.float32) for k, blob in rows}
    assert np.array_equal(stored[key(DOCUMENT, PASSAGES[1])], expected[2])


@pytest.mark.id("tst_f5j0ah")
def test_missing(model, tmp_path):
    """Only the texts the file lacks are sent, in order and in batches"""
    model.embeds(vector)
    questions = [f"Question {number}" for number in range(40)]
    with Cache(tmp_path / "vectors.sqlite") as cache:
        cache.vectors(model.client(), PASSAGES[:2], DOCUMENT)
        model.requests.clear()
        cache.vectors(model.client(), PASSAGES + questions, DOCUMENT, batch=32)
        assert [len(request.body["input"]) for request in model.requests] == [32, 9]
        assert sent(model) == [DOCUMENT + text for text in PASSAGES[3:] + questions]
        cache.vectors(model.client(), PASSAGES[:1], QUERY)
    assert sent(model)[-1] == QUERY + PASSAGES[0]


@pytest.mark.id("tst_w9e4qb")
def test_failure(tmp_path):
    """A failure keeps the batches before it"""
    bodies = []

    def answer(request):
        body = json.loads(request.content)
        bodies.append(body)
        if len(bodies) == 2:
            return httpx.Response(
                503, json={"error": {"code": 503, "message": "Loading model"}}
            )
        data = [
            {"embedding": vector(text), "index": index, "object": "embedding"}
            for index, text in enumerate(body["input"])
        ]
        return httpx.Response(200, json={"data": data, "object": "list"})

    client = httpx.Client(
        base_url="http://model.test/v1", transport=httpx.MockTransport(answer)
    )
    texts = [f"Passage {number}" for number in range(70)]
    with Cache(tmp_path / "vectors.sqlite") as cache:
        with pytest.raises(ModelError):
            cache.vectors(client, texts, DOCUMENT, batch=32)
        found = cache.vectors(client, texts, DOCUMENT, batch=32)
    assert [len(body["input"]) for body in bodies] == [32, 32, 32, 6]
    assert bodies[2]["input"][0] == DOCUMENT + texts[32]
    assert found.shape == (70, 3)


@pytest.mark.id("tst_u3m6gz")
def test_no_texts(model, tmp_path):
    """No texts, no request"""
    with Cache(tmp_path / "vectors.sqlite") as cache:
        found = cache.vectors(model.client(), [], QUERY)
    assert model.requests == []
    assert found.shape == (0, 0)
