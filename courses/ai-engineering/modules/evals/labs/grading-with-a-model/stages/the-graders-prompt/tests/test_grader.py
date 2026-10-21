import json
from pathlib import Path

import httpx
import pytest

from grader import prompt, risk, template

RECORDED = json.loads(Path("references/prompts.json").read_text(encoding="utf-8"))[
    "cases"
]
CHAT = template(Path("data/tokenizer_config.json"))


@pytest.mark.id("tst_3k8ieg")
def test_prompts():
    """Renders the prompts transformers renders from the model's own template"""
    for case in RECORDED:
        found = prompt(CHAT, case["context"], case["reply"], case["today"])
        assert found == case["prompt"]


@pytest.mark.id("tst_0rjv1e")
def test_parts_of_the_prompt():
    """Puts the context, the reply and the date where the template asks for them"""
    found = prompt(CHAT, "We open at 9.", "We open at 10.", "May 01, 2027")
    assert "Today's Date: May 01, 2027." in found
    assert "Context: We open at 9.\nAssistant Message: We open at 10.\n" in found
    assert found.endswith("<|start_of_role|>assistant<|end_of_role|>")


@pytest.mark.id("tst_dyb0yg")
def test_risk(model):
    """Reads the probability of Yes over Yes or No from the likeliest first tokens"""
    model.says("No", probabilities=[{"No": 0.9, "Yes": 0.05, " Yes": 0.03, "no": 0.02}])
    found = risk(model.client(), "Grounded?")
    assert found == pytest.approx((0.05 + 0.03) / 1.0)
    body = model.requests[0].body
    assert model.requests[0].path == "/v1/completions"
    assert body["model"] == "Granite-Guardian-3.1-2B"
    assert body["prompt"] == "Grounded?"
    assert (body["max_tokens"], body["temperature"], body["logprobs"]) == (1, 0, 20)


@pytest.mark.id("tst_qiwlwm")
def test_risk_without_other_tokens(model):
    """Leaves out the likeliest tokens that are neither Yes nor No"""
    weighed = {"Yes": 0.6, "No": 0.2, "Maybe": 0.15, "N": 0.05}
    model.says("Yes", probabilities=[weighed])
    assert risk(model.client(), "Grounded?") == pytest.approx(0.6 / 0.8)


@pytest.mark.id("tst_vjy81k")
def test_refused(model):
    """Raises when the server refuses the request"""
    model.fails(503, "Loading model")
    with pytest.raises(httpx.HTTPStatusError):
        risk(model.client(), "Grounded?")
