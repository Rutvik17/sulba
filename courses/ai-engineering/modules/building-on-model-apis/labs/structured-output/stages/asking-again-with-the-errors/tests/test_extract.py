import json

import pytest

from extract import MODEL, ModelError, NoMatch, ask_for
from schema import errors

BOOKING = {
    "type": "object",
    "properties": {
        "name": {"type": "string", "minLength": 1, "maxLength": 60},
        "bike": {"enum": ["road", "mountain", "city", "cargo", "e-bike"]},
        "service": {"enum": ["puncture", "brakes", "gears", "full service"]},
        "date": {"type": "string", "format": "date"},
        "time": {"type": "string", "pattern": "^(09|1[0-6]):[03]0$"},
        "bikes": {"type": "integer", "minimum": 1, "maximum": 3},
        "phone": {"type": ["string", "null"], "pattern": "^\\+?[0-9 ]{7,15}$"},
        "notes": {"type": "string", "maxLength": 500},
    },
    "required": ["name", "bike", "service", "date", "time", "bikes", "phone", "notes"],
    "additionalProperties": False,
}
EMAIL = [
    {
        "role": "system",
        "content": "Fill in the shop's booking form from the customer's email.",
    },
    {
        "role": "user",
        "content": "Hi, could you look at my city bike's brakes on Saturday 24 October at "
        "10.30? Ana Silva, 07700 900123",
    },
]
BOOKED = {
    "name": "Ana Silva",
    "bike": "city",
    "service": "brakes",
    "date": "2026-10-24",
    "time": "10:30",
    "bikes": 1,
    "phone": "07700 900123",
    "notes": "",
}


def feedback(problems):
    lines = "".join(f"- {problem}\n" for problem in problems)
    return f"Your reply doesn't match the schema:\n{lines}Reply again with only the corrected JSON."


@pytest.mark.id("tst_anesjk")
def test_request(model):
    """The request holds the reply to the schema, strictly, under its name"""
    model.says(json.dumps(BOOKED))
    ask_for(model.client(), EMAIL, BOOKING, "booking", max_tokens=300)
    [request] = model.requests
    assert request.path == "/v1/chat/completions"
    assert request.body["model"] == MODEL
    assert request.body["messages"] == EMAIL
    assert request.body["max_completion_tokens"] == 300
    assert request.body["response_format"] == {
        "type": "json_schema",
        "json_schema": {"name": "booking", "schema": BOOKING, "strict": True},
    }


@pytest.mark.id("tst_ibqhxu")
def test_match(model):
    """A reply that matches comes back as the value it holds"""
    model.says(json.dumps(BOOKED))
    assert ask_for(model.client(), EMAIL, BOOKING, "booking") == BOOKED
    assert len(model.requests) == 1


@pytest.mark.id("tst_r5niip")
def test_errors_go_back(model):
    """A reply that fails the schema goes back as the model's, with its errors as the user's"""
    wrong = json.dumps({**BOOKED, "time": "10.30", "bikes": "1"})
    model.says(wrong)
    model.says(json.dumps(BOOKED))
    assert ask_for(model.client(), EMAIL, BOOKING, "booking") == BOOKED
    found = errors(json.loads(wrong), BOOKING)
    problems = [f"{error.path}: {error.message}" for error in found]
    assert len(problems) == 2
    assert model.requests[1].body["messages"] == [
        *EMAIL,
        {"role": "assistant", "content": wrong},
        {"role": "user", "content": feedback(problems)},
    ]
    assert EMAIL[-1]["role"] == "user" and len(EMAIL) == 2


@pytest.mark.id("tst_8xb7o1")
def test_not_json(model):
    """A reply that isn't JSON says so, with where the JSON went wrong"""
    model.says("Sure! Here's the booking: " + json.dumps(BOOKED))
    model.says(json.dumps(BOOKED))
    ask_for(model.client(), EMAIL, BOOKING, "booking")
    asked = model.requests[1].body["messages"][-1]["content"]
    assert asked == feedback(
        ["The reply isn't JSON: Expecting value: line 1 column 1 (char 0)"]
    )


@pytest.mark.id("tst_hwo92e")
def test_cut_off(model):
    """A reply cut off at its token limit is never read as JSON"""
    model.says(
        '{"name": "Ana Silva", "bike": "city", "service": "bra', finish_reason="length"
    )
    model.says('{"name": "Ana"}', finish_reason="length")
    model.says(json.dumps(BOOKED))
    assert ask_for(model.client(), EMAIL, BOOKING, "booking") == BOOKED
    for request in model.requests[1:]:
        asked = request.body["messages"][-1]["content"]
        assert asked == feedback(["The reply was cut off at its token limit."])


@pytest.mark.id("tst_hrwqg5")
def test_gives_up(model):
    """After its last attempt, NoMatch says what was wrong with the last reply"""
    for reply in [
        "no",
        json.dumps({**BOOKED, "bike": "bmx"}),
        json.dumps({**BOOKED, "bikes": 0}),
    ]:
        model.says(reply)
    with pytest.raises(NoMatch) as raised:
        ask_for(model.client(), EMAIL, BOOKING, "booking", attempts=3)
    assert len(model.requests) == 3
    [problem] = raised.value.problems
    assert problem.startswith("$.bikes: ")


@pytest.mark.id("tst_ee5faz")
def test_model_errors(model):
    """An error from the API is raised at once, with its status and message"""
    model.fails(503, "Loading model")
    with pytest.raises(ModelError) as raised:
        ask_for(model.client(), EMAIL, BOOKING, "booking")
    assert (raised.value.status, raised.value.message) == (503, "Loading model")
    assert len(model.requests) == 1
