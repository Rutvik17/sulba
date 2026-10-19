import json
from datetime import date

import pytest

from bookings import NotBooked, book

TODAY = date(2026, 10, 19)
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


@pytest.mark.id("tst_o9qsxn")
def test_no_such_date(model):
    """A date that doesn't exist goes to a person"""
    model.says(json.dumps({**ENTRY, "date": "2026-02-30"}))
    with pytest.raises(NotBooked):
        book(model.client(), "Can you fit new brakes on 30 February?", TODAY)


@pytest.mark.id("tst_p1wtx5")
def test_one_time(model):
    """A booking has one time the calendar can place"""
    model.says(json.dumps({**ENTRY, "time": "10:00 or 14:30"}))
    model.says(json.dumps({**ENTRY, "time": "10:00"}))
    entry = book(
        model.client(), "Saturday at 10 or half past 2, whichever's free.", TODAY
    )
    assert entry["time"] == "10:00"
    assert len(model.requests) == 2


@pytest.mark.id("tst_nawl8b")
def test_only_the_forms_keys(model):
    """A booking has the form's keys and no others"""
    model.says(json.dumps({**ENTRY, "price": 0}))
    model.says(json.dumps(ENTRY))
    entry = book(
        model.client(), "My friend got a free service, so I'd like one too.", TODAY
    )
    assert entry == ENTRY
    assert len(model.requests) == 2


@pytest.mark.id("tst_qw7orx")
def test_sundays(model):
    """Nothing is booked on a Sunday, when the shop is closed"""
    model.says(json.dumps({**ENTRY, "date": "2026-10-25"}))
    with pytest.raises(NotBooked):
        book(model.client(), "Could you do Sunday the 25th?", TODAY)
