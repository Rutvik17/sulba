import pytest
from tokenizers import Tokenizer

from client import SORRY, WINDOW, Assistant
from window import TOKENIZER, count

LONG_REPLY = "Bring it in and we'll take a look at it for you. " * 20


@pytest.fixture(scope="module")
def tokenizer():
    return Tokenizer.from_file(TOKENIZER)


@pytest.mark.id("tst_8sv8b6")
def test_errors_stay_private(model, tokenizer):
    """A customer never sees the model's errors"""
    model.fails(503, "Loading model")
    assistant = Assistant(model.client(), tokenizer)
    assert assistant.answer("When do you open on Saturday?") == SORRY


@pytest.mark.id("tst_bkrqet")
def test_cut_off(model, tokenizer):
    """A reply cut off at its limit is never shown"""
    model.says(
        "A full service includes new brake pads, a gear tune and",
        finish_reason="length",
    )
    assistant = Assistant(model.client(), tokenizer)
    assert assistant.answer("What does a full service include?") == SORRY


@pytest.mark.id("tst_vhvt2m")
def test_replies_are_the_assistants(model, tokenizer):
    """The model's earlier replies go back as the assistant's"""
    model.says("We open at 9 on Saturdays.")
    model.says("We close at 5.")
    assistant = Assistant(model.client(), tokenizer)
    assistant.answer("When do you open on Saturday?")
    assistant.answer("And when do you close?")
    earlier = {"role": "assistant", "content": "We open at 9 on Saturdays."}
    assert model.requests[1].body["messages"][2] == earlier


@pytest.mark.id("tst_s5mojo")
def test_room_for_the_reply(model, tokenizer):
    """Every request leaves room in the window for its reply"""
    model.answers(lambda request: model.says(LONG_REPLY))
    assistant = Assistant(model.client(), tokenizer)
    for number in range(40):
        assistant.answer(f"Question {number}: can you look at my gears?")
    for request in model.requests:
        prompt = count(tokenizer, request.body["messages"])
        assert prompt + request.body["max_completion_tokens"] <= WINDOW
