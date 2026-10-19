import json
from datetime import date

import pytest

from bookings import FORM, INSTRUCTIONS, NotBooked, book

TODAY = date(2026, 10, 19)
EMAIL = (
    "Hi, could you look at my city bike's brakes on Saturday 24 October at 10.30? "
    "Ana Silva, 07700 900123"
)
ENTRY = {
    "name": "Ana Silva",
    "bike": "city",
    "service": "brakes",
    "date": "2026-10-24",
    "time": "10:30",
    "bikes": 1,
    "phone": "07700 900123",
    "notes": "",
}


@pytest.mark.id("tst_kbjzlr")
def test_books(model):
    """An email's booking, filled in on the shop's form"""
    model.says(json.dumps(ENTRY))
    assert book(model.client(), EMAIL, TODAY) == ENTRY
    [request] = model.requests
    assert request.body["messages"] == [
        {"role": "system", "content": INSTRUCTIONS.format(today="2026-10-19")},
        {"role": "user", "content": EMAIL},
    ]
    assert request.body["response_format"]["json_schema"]["schema"] == FORM


@pytest.mark.id("tst_f1y1sv")
def test_past(model):
    """A date that has passed isn't booked"""
    model.says(json.dumps({**ENTRY, "date": "2026-10-12"}))
    with pytest.raises(NotBooked):
        book(model.client(), EMAIL, TODAY)


@pytest.mark.id("tst_8ojmqu")
def test_asks_again(model):
    """A reply that doesn't fit the form is sent back with its errors"""
    model.says(json.dumps({**ENTRY, "bikes": 0}))
    model.says(json.dumps(ENTRY))
    assert book(model.client(), EMAIL, TODAY) == ENTRY
    assert len(model.requests) == 2


@pytest.mark.id("tst_mqs3os")
def test_gives_up(model):
    """When no reply fits the form, the email goes to a person"""
    for _ in range(3):
        model.says(json.dumps({**ENTRY, "bike": "bmx"}))
    with pytest.raises(NotBooked):
        book(model.client(), EMAIL, TODAY)
