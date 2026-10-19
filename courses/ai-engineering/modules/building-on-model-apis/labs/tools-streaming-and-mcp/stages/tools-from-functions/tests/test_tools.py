import json
from typing import Annotated, Literal

import pytest

from tools import describe, run

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
Day = Literal[
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"
]
Service = Literal["puncture", "brakes", "gears", "full service"]


def opening_hours(day: Day) -> str:
    """The shop's opening hours on a day of the week."""
    return "Closed" if day == "Sunday" else "9:00 to 17:00"


def repair_price(service: Service, bikes: Annotated[int, "How many bikes"]) -> float:
    """The price of a repair, in pounds.

    A full service includes every other repair."""
    prices = {"puncture": 12.0, "brakes": 18.0, "gears": 25.0, "full service": 60.0}
    if bikes < 1:
        raise ValueError("A repair is for one bike or more.")
    return prices[service] * bikes


def next_booking(name: str, phone: str | None, day: Day | None) -> dict:
    """The customer's next booking, found by their name and phone, from a day on."""
    return {"name": name, "day": day or "Monday", "time": "10:30"}


def parts(names: list[str], in_stock: bool) -> list[dict]:
    """The parts the shop has, by name."""
    return [{"name": each, "in_stock": in_stock} for each in names]


def call(name, arguments, number=1):
    text = arguments if isinstance(arguments, str) else json.dumps(arguments)
    return {
        "id": f"call_{number}",
        "type": "function",
        "function": {"name": name, "arguments": text},
    }


FUNCTIONS = {
    each.__name__: each for each in [opening_hours, repair_price, next_booking]
}


@pytest.mark.id("tst_cmd7n5")
def test_tool():
    """A function's tool: its name, its docstring and a strict schema of its parameters"""
    assert describe(opening_hours) == {
        "type": "function",
        "function": {
            "name": "opening_hours",
            "description": "The shop's opening hours on a day of the week.",
            "parameters": {
                "type": "object",
                "properties": {"day": {"type": "string", "enum": DAYS}},
                "required": ["day"],
                "additionalProperties": False,
            },
            "strict": True,
        },
    }


@pytest.mark.id("tst_g04nfp")
def test_types():
    """Each type's schema, with a parameter's description from Annotated"""
    price = describe(repair_price)["function"]
    assert price["description"] == (
        "The price of a repair, in pounds.\n\nA full service includes every other repair."
    )
    assert price["parameters"]["properties"] == {
        "service": {
            "type": "string",
            "enum": ["puncture", "brakes", "gears", "full service"],
        },
        "bikes": {"type": "integer", "description": "How many bikes"},
    }
    assert describe(parts)["function"]["parameters"]["properties"] == {
        "names": {"type": "array", "items": {"type": "string"}},
        "in_stock": {"type": "boolean"},
    }


@pytest.mark.id("tst_wsmyo4")
def test_optional():
    """A parameter that can be None is required, with null among its types"""
    found = describe(next_booking)["function"]["parameters"]
    assert found["properties"] == {
        "name": {"type": "string"},
        "phone": {"type": ["string", "null"]},
        "day": {"type": ["string", "null"], "enum": [*DAYS, None]},
    }
    assert found["required"] == ["name", "phone", "day"]


@pytest.mark.id("tst_rh1ypz")
def test_refused():
    """A name the API won't take, or a type with no schema here, is refused"""

    def réservation(day: Day) -> str:
        """Books a day."""
        return day

    def notes(text: dict) -> str:
        """Keeps notes."""
        return ""

    with pytest.raises(ValueError):
        describe(réservation)
    with pytest.raises(TypeError):
        describe(notes)


@pytest.mark.id("tst_xijthk")
def test_run():
    """A call's result goes back as the tool's message, as JSON, with the call's id"""
    found = run(FUNCTIONS, call("repair_price", {"service": "brakes", "bikes": 2}, 7))
    assert found == {"role": "tool", "tool_call_id": "call_7", "content": "36.0"}
    found = run(
        FUNCTIONS, call("next_booking", {"name": "Zoë", "phone": None, "day": None})
    )
    assert json.loads(found["content"]) == {
        "name": "Zoë",
        "day": "Monday",
        "time": "10:30",
    }
    assert "Zoë" in found["content"]


@pytest.mark.id("tst_rmbgfy")
def test_errors():
    """A call that can't run gets an error the model can read, and never raises"""
    wrong = [
        call("opening_times", {"day": "Monday"}),
        call("opening_hours", '{"day": "Monday"'),
        call("opening_hours", {"day": "Monday", "week": 2}),
        call("opening_hours", {}),
        call("opening_hours", "[]"),
        call("repair_price", {"service": "brakes", "bikes": 0}),
    ]
    for each in wrong:
        found = run(FUNCTIONS, each)
        assert found["role"] == "tool" and found["tool_call_id"] == "call_1"
        error = json.loads(found["content"])["error"]
        assert isinstance(error, str) and error, each
    zero = run(FUNCTIONS, wrong[-1])
    assert json.loads(zero["content"]) == {"error": "A repair is for one bike or more."}
