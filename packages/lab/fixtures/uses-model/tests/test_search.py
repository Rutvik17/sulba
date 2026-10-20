import base64
import struct

import httpx
import openai
import pytest

from search import embed, rerank

HOURS = "We open at 9 and close at 6."
REPAIRS = "Most repairs are done the same day."
VECTORS = {
    HOURS: [0.6, 0.8, 0.0],
    REPAIRS: [0.0, 0.6, 0.8],
    "When do you open?": [0.8, 0.6, 0.0],
}


@pytest.mark.id("tst_mdl016")
def test_embeddings(model):
    """Embeds each text with the vector the test scripted, in llama-server's form"""
    model.embeds(VECTORS)
    assert embed(model.client(), [HOURS, REPAIRS]) == [VECTORS[HOURS], VECTORS[REPAIRS]]
    reply = model.client().post("/embeddings", json={"input": [HOURS]}).json()
    assert reply == {
        "model": "scripted",
        "object": "list",
        "usage": {"prompt_tokens": 0, "total_tokens": 0},
        "data": [{"embedding": [0.6, 0.8, 0.0], "index": 0, "object": "embedding"}],
    }
    assert model.requests[0].path == "/v1/embeddings"


@pytest.mark.id("tst_mdl017")
def test_embeddings_of_one_text(model):
    """Embeds a text given alone, from a function, and counts its tokens when told how"""
    model.embeds(lambda text: [float(len(text)), 1.0], tokens=lambda text: len(text.split()))
    body = {"model": "shop-embeddings", "input": "When do you open?"}
    reply = model.client().post("/embeddings", json=body).json()
    assert [item["embedding"] for item in reply["data"]] == [[17.0, 1.0]]
    assert reply["usage"] == {"prompt_tokens": 4, "total_tokens": 4}
    assert reply["model"] == "shop-embeddings"


@pytest.mark.id("tst_mdl018")
def test_embeddings_in_base64(model):
    """Sends each embedding as float32 in base64 when the request asks for it"""
    model.embeds(VECTORS)
    body = {"input": [HOURS], "encoding_format": "base64"}
    [item] = model.client().post("/embeddings", json=body).json()["data"]
    assert item["encoding_format"] == "base64"
    numbers = struct.unpack("<3f", base64.b64decode(item["embedding"]))
    assert numbers == struct.unpack("<3f", struct.pack("<3f", 0.6, 0.8, 0.0))


@pytest.mark.id("tst_mdl019")
def test_embeddings_through_openai(model):
    """Gives the openai package embeddings it reads"""
    model.embeds(VECTORS)
    shop = openai.OpenAI(
        base_url=model.url, api_key="test", http_client=model.client(), max_retries=0
    )
    reply = shop.embeddings.create(model="shop-embeddings", input=[HOURS, REPAIRS])
    assert [item.embedding for item in reply.data] == [
        pytest.approx(VECTORS[HOURS]),
        pytest.approx(VECTORS[REPAIRS]),
    ]


@pytest.mark.id("tst_mdl020")
def test_rerank(model):
    """Ranks documents by the scores the test scripted, highest first and at most top_n"""
    scores = {("When do you open?", HOURS): 0.98, ("When do you open?", REPAIRS): 0.02}
    model.ranks(scores)
    client = model.client()
    assert rerank(client, "When do you open?", [REPAIRS, HOURS]) == [
        (1, 0.98),
        (0, 0.02),
    ]
    assert rerank(client, "When do you open?", [REPAIRS, HOURS], top_n=1) == [(1, 0.98)]
    reply = client.post("/rerank", json={"query": "When do you open?", "documents": [HOURS]})
    assert reply.json() == {
        "model": "scripted",
        "object": "list",
        "usage": {"prompt_tokens": 0, "total_tokens": 0},
        "results": [{"index": 0, "relevance_score": 0.98}],
    }
    tei = client.post("/rerank", json={"query": "When do you open?", "texts": [REPAIRS, HOURS]})
    assert tei.json() == [{"index": 1, "score": 0.98}, {"index": 0, "score": 0.02}]


@pytest.mark.id("tst_mdl024")
def test_rerank_top_n(model):
    """Reads top_n as llama-server does: a number cut to an integer, a boolean as 1 or 0"""
    model.ranks(lambda query, document: 0.9 if document == HOURS else 0.1)
    client = model.client()
    kept = {}
    for top_n in [True, 1.9, "1", None, -1, 0]:
        body = {"query": "When do you open?", "documents": [REPAIRS, HOURS], "top_n": top_n}
        kept[repr(top_n)] = len(client.post("/rerank", json=body).json()["results"])
    assert kept == {"True": 1, "1.9": 1, "'1'": 2, "None": 2, "-1": 0, "0": 0}


@pytest.mark.id("tst_mdl021")
def test_refusals(model):
    """Refuses the embeddings and rerank requests llama-server refuses, in its words"""
    model.embeds(VECTORS)
    model.ranks(lambda query, document: 0.5)
    client = model.client()
    refused = [
        client.post("/embeddings", json={"texts": [HOURS]}),
        client.post("/embeddings", json={"content": HOURS}),
        client.post("/embeddings", json={"input": [HOURS], "encoding_format": "int8"}),
        client.post("/embeddings", json={"input": []}),
        client.post("/rerank", json={"documents": [HOURS]}),
        client.post("/rerank", json={"query": "Open?", "documents": []}),
    ]
    assert [(reply.status_code, reply.json()["error"]["message"]) for reply in refused] == [
        (400, '"input" or "content" must be provided'),
        (400, 'The scripted model embeds text given as "input", as OpenAI\'s API gives it.'),
        (400, "The format to return the embeddings in. Can be either float or base64"),
        (400, '"input" must not be empty'),
        (400, '"query" must be provided'),
        (400, '"documents" must be a non-empty string array'),
    ]


@pytest.mark.id("tst_mdl022")
def test_failure_answers_next_request(model):
    """Answers the next request with the failure the test scripted, whatever it asks"""
    model.embeds(VECTORS)
    model.fails(503, "Loading model")
    with pytest.raises(httpx.HTTPStatusError) as raised:
        embed(model.client(), [HOURS])
    assert raised.value.response.status_code == 503
    assert embed(model.client(), [HOURS]) == [VECTORS[HOURS]]


@pytest.mark.id("tst_mdl023")
def test_no_vector(model):
    """Stops code that embeds a text the test scripted no vector for"""
    model.embeds(VECTORS)
    embed(model.client(), ["Do you sell bells?"])
