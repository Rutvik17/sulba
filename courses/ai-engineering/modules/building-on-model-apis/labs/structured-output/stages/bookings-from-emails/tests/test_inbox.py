import json
from datetime import date

import pytest

from inbox import Booking, NotBooked, book

TODAY = date(2026, 10, 19)
EMAIL = (
    "Hi, could you look at my city bike's brakes on Saturday 24 October at 10.30? "
    "Ana Silva, 07700 900123"
)
FOUND = {
    "name": "Ana Silva",
    "bike": "city",
    "service": "brakes",
    "date": "2026-10-24",
    "time": "10:30",
    "bikes": 1,
    "phone": "07700 900123",
    "notes": "",
}


@pytest.mark.id("tst_521tjz")
def test_books(model):
    """An email that asks for a booking gets it"""
    model.says(json.dumps({"booking": FOUND}))
    assert book(model.client(), EMAIL, TODAY) == Booking(
        name="Ana Silva",
        bike="city",
        service="brakes",
        day=date(2026, 10, 24),
        time="10:30",
        bikes=1,
        phone="07700 900123",
        notes="",
    )


@pytest.mark.id("tst_62gdrd")
def test_no_booking(model):
    """An email that asks for no booking goes to a person"""
    model.says(json.dumps({"booking": None}))
    with pytest.raises(NotBooked):
        book(model.client(), "Do you sell inner tubes?", TODAY)
