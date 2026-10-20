import math

import pytest

from grade import grounded

WEIGHED = {"No": 0.8, "Yes": 0.15, "Maybe": 0.05}


@pytest.mark.id("tst_mdl025")
def test_completion_form(model):
    """Completes a prompt with the reply the test scripted, in the completions API's form"""
    model.says("Yes", usage=(30, 1))
    reply = model.client().post("/completions", json={"prompt": "Grounded?"}).json()
    assert reply == {
        "choices": [{"text": "Yes", "index": 0, "logprobs": None, "finish_reason": "stop"}],
        "created": 0,
        "model": "scripted",
        "object": "text_completion",
        "usage": {"prompt_tokens": 30, "completion_tokens": 1, "total_tokens": 31},
        "id": "chatcmpl-1",
    }
    assert model.requests[0].path == "/v1/completions"


@pytest.mark.id("tst_mdl026")
def test_completion_logprobs(model):
    """Gives each token's logprob and the likeliest tokens for its place, as many as asked"""
    model.says("No", probabilities=[WEIGHED])
    body = {"model": "grader", "prompt": "Grounded?", "logprobs": 2}
    [token] = (
        model.client().post("/completions", json=body).json()["choices"][0]["logprobs"]["content"]
    )
    assert token == {
        "id": 0,
        "token": "No",
        "bytes": [78, 111],
        "logprob": math.log(0.8),
        "top_logprobs": [
            {"id": 0, "token": "No", "bytes": [78, 111], "logprob": math.log(0.8)},
            {"id": 1, "token": "Yes", "bytes": [89, 101, 115], "logprob": math.log(0.15)},
        ],
    }


@pytest.mark.id("tst_mdl027")
def test_grounded(model):
    """Gives code the probabilities it reads a verdict from"""
    model.says("No", probabilities=[WEIGHED])
    assert grounded(model.client(), "Grounded?") == pytest.approx(0.8 / 0.95)
    assert model.requests[0].body["logprobs"] == 5


@pytest.mark.id("tst_mdl028")
def test_chat_logprobs(model):
    """Gives a chat reply's probabilities when asked, after sampling when asked that"""
    model.says("We open", " at 9.")
    model.says(
        "We open",
        " at 9.",
        probabilities=[{"We open": 0.6, "We close": 0.4}, {" at 9.": 1.0}],
    )
    plain = model.client().post("/chat/completions", json={"messages": []}).json()
    assert "logprobs" not in plain["choices"][0]
    body = {"messages": [], "logprobs": True, "top_logprobs": 1, "post_sampling_probs": True}
    reply = model.client().post("/chat/completions", json=body).json()
    assert reply["choices"][0]["message"]["content"] == "We open at 9."
    assert [
        (token["token"], token["prob"], [top["token"] for top in token["top_probs"]])
        for token in reply["choices"][0]["logprobs"]["content"]
    ] == [("We open", 0.6, ["We open"]), (" at 9.", 1.0, [" at 9."])]


@pytest.mark.id("tst_mdl029")
def test_completion_refusals(model):
    """Refuses requests llama-server refuses, in its words"""
    client = model.client()
    missing = client.post("/completions", json={"model": "grader"})
    assert missing.status_code == 400
    assert missing.json()["error"]["message"] == (
        "[json.exception.out_of_range.403] key 'prompt' not found"
    )
    early = client.post("/chat/completions", json={"messages": [], "top_logprobs": 2})
    assert early.json()["error"]["message"] == "top_logprobs requires logprobs to be set to true"
    model.says("No")
    with pytest.raises(BaseException, match="no probabilities"):
        client.post("/completions", json={"prompt": "Grounded?", "logprobs": 2})
    with pytest.raises(ValueError, match="leave it out"):
        model.says("No", probabilities=[{"Yes": 1.0}])
