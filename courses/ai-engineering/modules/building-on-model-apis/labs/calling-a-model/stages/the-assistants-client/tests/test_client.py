import pytest
from tokenizers import Tokenizer

from client import INSTRUCTIONS, WINDOW, Assistant
from window import TOKENIZER, count

LONG_REPLY = "Bring it in and we'll take a look at it for you. " * 20


@pytest.fixture(scope="module")
def tokenizer():
    return Tokenizer.from_file(TOKENIZER)


@pytest.mark.id("tst_b60b5n")
def test_answers(model, tokenizer):
    """The model's answer, after the shop's instructions"""
    model.says("We open at 9 on Saturdays.")
    assistant = Assistant(model.client(), tokenizer)
    assert (
        assistant.answer("When do you open on Saturday?")
        == "We open at 9 on Saturdays."
    )
    assert model.requests[0].body["messages"] == [
        {"role": "system", "content": INSTRUCTIONS},
        {"role": "user", "content": "When do you open on Saturday?"},
    ]


@pytest.mark.id("tst_gaozkg")
def test_remembers(model, tokenizer):
    """Each question goes with the conversation before it"""
    model.says("We open at 9 on Saturdays.")
    model.says("We close at 5.")
    assistant = Assistant(model.client(), tokenizer)
    assistant.answer("When do you open on Saturday?")
    assert assistant.answer("And when do you close?") == "We close at 5."
    assert len(model.requests[1].body["messages"]) == 4


@pytest.mark.id("tst_u34vqh")
def test_long_conversation(model, tokenizer):
    """A long conversation still fits in the model's window"""
    model.answers(lambda request: model.says(LONG_REPLY))
    assistant = Assistant(model.client(), tokenizer)
    for number in range(40):
        assert (
            assistant.answer(f"Question {number}: can you look at my gears?")
            == LONG_REPLY
        )
    for request in model.requests:
        assert count(tokenizer, request.body["messages"]) <= WINDOW
