import httpx
import numpy as np
import pytest

from embed import BATCH, DOCUMENT, MODEL, QUERY, ModelError, embed

PASSAGES = [
    "You can apply for disability benefits online.",
    "Bring proof of your age to the office.",
    "Renew your license before it expires.",
]
TOO_LONG = (
    "input (2306 tokens) is too large to process. increase the physical batch size "
    "(current batch size: 2048)"
)


def vector(text):
    """A short vector of its own for each text, from its length and first letter."""
    return [len(text) / 100, ord(text[0]) / 100, 0.5]


@pytest.mark.id("tst_2wq8kd")
def test_request(model):
    """One POST to /embeddings with the model and each text after the prefix"""
    model.embeds(vector)
    embed(model.client(), PASSAGES, DOCUMENT)
    [request] = model.requests
    assert (request.method, request.path) == ("POST", "/v1/embeddings")
    assert request.body["model"] == MODEL
    assert request.body["input"] == [DOCUMENT + text for text in PASSAGES]


@pytest.mark.id("tst_8fj2mz")
def test_prefixes():
    """The prefixes of the model's card"""
    assert (DOCUMENT, QUERY) == ("search_document: ", "search_query: ")


@pytest.mark.id("tst_q7c1xv")
def test_vectors(model):
    """Each text's vector, as a float32 row in the texts' order"""
    model.embeds(vector)
    found = embed(model.client(), PASSAGES, QUERY)
    assert found.dtype == np.float32
    expected = np.array([vector(QUERY + text) for text in PASSAGES], dtype=np.float32)
    assert np.array_equal(found, expected)


@pytest.mark.id("tst_m3k9tr")
def test_batches(model):
    """At most batch texts a request, in order"""
    model.embeds(vector)
    texts = [f"Question {number}" for number in range(70)]
    found = embed(model.client(), texts, QUERY, batch=32)
    assert [len(request.body["input"]) for request in model.requests] == [32, 32, 6]
    sent = [text for request in model.requests for text in request.body["input"]]
    assert sent == [QUERY + text for text in texts]
    assert found.shape == (70, 3)
    assert BATCH == 32


@pytest.mark.id("tst_5nd0ew")
def test_no_texts(model):
    """No texts, no request"""
    found = embed(model.client(), [], DOCUMENT)
    assert model.requests == []
    assert found.shape == (0, 0)
    assert found.dtype == np.float32


@pytest.mark.id("tst_h4z8ub")
def test_errors(model):
    """An error's status and the message from its body"""
    model.embeds(vector)
    model.fails(500, TOO_LONG)
    with pytest.raises(ModelError) as raised:
        embed(model.client(), PASSAGES, DOCUMENT)
    assert (raised.value.status, raised.value.message) == (500, TOO_LONG)
    transport = httpx.MockTransport(
        lambda request: httpx.Response(502, text="Bad Gateway")
    )
    client = httpx.Client(base_url="http://model.test/v1", transport=transport)
    with pytest.raises(ModelError) as raised:
        embed(client, PASSAGES, DOCUMENT)
    assert (raised.value.status, raised.value.message) == (502, "Bad Gateway")
