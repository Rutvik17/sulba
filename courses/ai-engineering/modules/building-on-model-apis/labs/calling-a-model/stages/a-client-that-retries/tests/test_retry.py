import pytest

from chat import Reply
from retry import ask_within

QUESTION = [{"role": "user", "content": "When do you open on Saturday?"}]


@pytest.mark.id("tst_xnrs0r")
def test_first_try(model, loop):
    """A reply on the first try comes back at once"""
    model.says("We open at 9 on Saturdays.", usage=(19, 9))
    reply = loop.run_until_complete(ask_within(model.async_client(), QUESTION, 64, 30))
    assert reply == Reply("We open at 9 on Saturdays.", "stop", 19, 9)
    assert len(model.requests) == 1 and loop.time() == 0


@pytest.mark.id("tst_7lb4g4")
def test_one_retry(model, loop):
    """A server still loading its model is asked again"""
    model.fails(503, "Loading model")
    model.says("We open at 9 on Saturdays.")
    reply = loop.run_until_complete(ask_within(model.async_client(), QUESTION, 64, 30))
    assert reply.text == "We open at 9 on Saturdays."
    assert len(model.requests) == 2 and 0 < loop.time() < 30
