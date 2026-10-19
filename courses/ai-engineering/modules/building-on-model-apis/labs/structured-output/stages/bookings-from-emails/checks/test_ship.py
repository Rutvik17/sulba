import json
from datetime import date

import pytest

from extract import ModelError
from inbox import Booking, NotBooked, book

TODAY = date(2026, 10, 19)
EMAIL = "Could you look at my city bike's brakes next Monday at 10.30? Ana Silva"
FOUND = {
    "name": "Ana Silva",
    "bike": "city",
    "service": "brakes",
    "date": "2026-10-26",
    "time": "10:30",
    "bikes": 1,
    "phone": None,
    "notes": "",
}
BOOKED = Booking(
    name="Ana Silva",
    bike="city",
    service="brakes",
    day=date(2026, 10, 26),
    time="10:30",
    bikes=1,
    phone=None,
    notes="",
)


def objects(schema):
    """Every schema with properties within schema, itself included."""
    found = []
    if isinstance(schema, dict):
        if "properties" in schema:
            found.append(schema)
        for key, value in schema.items():
            inside = value.values() if key == "properties" else [value]
            for each in inside:
                if isinstance(each, list):
                    found += [one for item in each for one in objects(item)]
                else:
                    found += objects(each)
    return found


def outcome(model, *replies):
    """What book does when the model gives these replies in turn, the last one from then on:
    the booking, or NotBooked."""
    start = len(model.requests)

    def answer(request):
        sent = len(model.requests) - start
        model.says(json.dumps(replies[min(sent, len(replies)) - 1]))

    model.answers(answer)
    try:
        return book(model.client(), EMAIL, TODAY)
    except NotBooked:
        return NotBooked


@pytest.mark.id("tst_y9e97c")
def test_strict_form(model):
    """Holds the reply to a strict form"""
    outcome(model, {"booking": FOUND})
    asked = model.requests[0].body["response_format"]
    assert asked["type"] == "json_schema" and asked["json_schema"]["strict"] is True
    schema = asked["json_schema"]["schema"]
    assert set(schema["properties"]) == {"booking"}
    for each in objects(schema):
        assert set(each["required"]) == set(each["properties"])
        assert each["additionalProperties"] is False


@pytest.mark.id("tst_yaj4pt")
def test_books_what_it_asks(model):
    """Books what the email asks"""
    assert outcome(model, {"booking": FOUND}) == BOOKED
    phoned = {**FOUND, "bikes": 2.0, "phone": "+44 7700 900123"}
    found = outcome(model, {"booking": phoned})
    assert found == Booking(
        **{**BOOKED.__dict__, "bikes": 2, "phone": "+44 7700 900123"}
    )
    assert type(found.bikes) is int
    saturday = {**FOUND, "date": "2026-10-31", "time": "12:30"}
    assert outcome(model, {"booking": saturday}).day == date(2026, 10, 31)
    last = {**FOUND, "date": "2026-11-16", "time": "16:30"}
    assert outcome(model, {"booking": last}).time == "16:30"


@pytest.mark.id("tst_8ylujc")
def test_sends_back_what_doesnt_fit(model):
    """Sends back a reply that doesn't fit the form"""
    wrong = [
        {"booking": {**FOUND, "price": 0}},
        {"booking": FOUND, "confirmed": True},
        {"booking": {**FOUND, "time": "10:00 or 14:30"}},
        {"booking": {**FOUND, "bikes": 1.5}},
        {"booking": {key: value for key, value in FOUND.items() if key != "notes"}},
        {"booking": {**FOUND, "bike": "bmx"}},
        {"booking": {**FOUND, "date": "26/10/2026"}},
        {"booking": "yes"},
        {},
    ]
    for reply in wrong:
        start = len(model.requests)
        assert outcome(model, reply, {"booking": FOUND}) == BOOKED, reply
        assert len(model.requests) - start == 2, reply
        assert model.requests[-1].body["messages"][-2] == {
            "role": "assistant",
            "content": json.dumps(reply),
        }


@pytest.mark.id("tst_n7xcdl")
def test_open_days_and_times(model):
    """Books only days and times the shop is open"""
    closed = [
        {**FOUND, "date": "2026-10-25"},
        {**FOUND, "date": "2026-10-31", "time": "14:00"},
        {**FOUND, "time": "17:00"},
        {**FOUND, "time": "08:30"},
        {**FOUND, "time": "10:15"},
        {**FOUND, "date": "2026-02-30"},
        {**FOUND, "date": "2026-10-12"},
        {**FOUND, "date": "2026-10-19"},
        {**FOUND, "date": "2026-11-17"},
    ]
    for each in closed:
        assert outcome(model, {"booking": each}, {"booking": FOUND}) in (
            NotBooked,
            BOOKED,
        ), each


@pytest.mark.id("tst_qg4fe6")
def test_says_no(model):
    """Says no when an email asks for no booking"""
    assert outcome(model, {"booking": None}) is NotBooked
    assert len(model.requests) == 1


@pytest.mark.id("tst_ey8o75")
def test_gives_up(model):
    """Gives up after its attempts, and raises the API's errors"""
    assert outcome(model, {"booking": "yes"}) is NotBooked
    assert len(model.requests) <= 3
    model.answers(lambda request: model.fails(503, "Loading model"))
    with pytest.raises(ModelError):
        book(model.client(), EMAIL, TODAY)
