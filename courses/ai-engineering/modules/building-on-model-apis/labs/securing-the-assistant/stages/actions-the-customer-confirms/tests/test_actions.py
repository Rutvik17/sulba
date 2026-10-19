import sqlite3
from datetime import datetime

import pytest

from actions import WAIT, Actions, Refused
from shop import SCHEMA

NOW = datetime(2026, 10, 20, 9, 0)
BOOKINGS = [
    ("B-1042", "C-7", "2026-10-24", "10:30", "brakes", "city", "", "booked"),
    ("B-1001", "C-7", "2026-10-03", "09:00", "puncture", "city", "", "done"),
    ("B-2001", "C-9", "2026-10-24", "11:00", "full service", "cargo", "", "booked"),
]


def shop():
    db = sqlite3.connect(":memory:")
    db.executescript(SCHEMA)
    db.executemany("INSERT INTO bookings VALUES (?, ?, ?, ?, ?, ?, ?, ?)", BOOKINGS)
    return db


def status(db, reference):
    return db.execute(
        "SELECT status FROM bookings WHERE reference = ?", (reference,)
    ).fetchone()[0]


@pytest.mark.id("tst_d5w359")
def test_proposal():
    """A proposal asks the customer, and changes nothing"""
    db = shop()
    action = Actions(db).propose_cancel("C-7", "B-1042", NOW)
    assert action.customer == "C-7" and action.reference == "B-1042"
    assert action.question == "Cancel booking B-1042, brakes on 2026-10-24 at 10:30?"
    assert action.expires == NOW + WAIT
    assert status(db, "B-1042") == "booked"


@pytest.mark.id("tst_bqgnja")
def test_confirmed_once():
    """The customer's confirmation cancels the booking, once"""
    db = shop()
    actions = Actions(db)
    action = actions.propose_cancel("C-7", "B-1042", NOW)
    assert (
        actions.confirm("C-7", action.id, NOW + WAIT / 2)
        == "Booking B-1042 is cancelled."
    )
    assert status(db, "B-1042") == "cancelled"
    with pytest.raises(Refused, match="That action isn't waiting for you."):
        actions.confirm("C-7", action.id, NOW + WAIT / 2)


@pytest.mark.id("tst_n1f84z")
def test_only_its_customer():
    """Only the customer an action is for can confirm it"""
    db = shop()
    actions = Actions(db)
    action = actions.propose_cancel("C-7", "B-1042", NOW)
    with pytest.raises(Refused, match="That action isn't waiting for you."):
        actions.confirm("C-9", action.id, NOW)
    assert status(db, "B-1042") == "booked"
    assert actions.confirm("C-7", action.id, NOW) == "Booking B-1042 is cancelled."


@pytest.mark.id("tst_gr7sbp")
def test_expires():
    """An action confirmed too late is refused, and gone"""
    db = shop()
    actions = Actions(db)
    action = actions.propose_cancel("C-7", "B-1042", NOW)
    with pytest.raises(Refused, match="That action has expired."):
        actions.confirm("C-7", action.id, NOW + WAIT)
    with pytest.raises(Refused, match="That action isn't waiting for you."):
        actions.confirm("C-7", action.id, NOW)
    assert status(db, "B-1042") == "booked"


@pytest.mark.id("tst_yn2lf8")
def test_unguessable_ids():
    """Each action's id is new and random"""
    actions = Actions(shop())
    ids = [actions.propose_cancel("C-7", "B-1042", NOW).id for _ in range(50)]
    assert len(set(ids)) == len(ids)
    assert all(len(id) >= 22 and "1042" not in id for id in ids)
    with pytest.raises(Refused):
        actions.confirm("C-7", "B-1042", NOW)


@pytest.mark.id("tst_efygrb")
def test_refused():
    """Only a booking of the customer's that's still booked can be cancelled"""
    db = shop()
    actions = Actions(db)
    for reference in ["B-2001", "B-1001", "B-9999"]:
        with pytest.raises(Refused, match=f"There's no booking {reference} to cancel."):
            actions.propose_cancel("C-7", reference, NOW)
    action = actions.propose_cancel("C-7", "B-1042", NOW)
    db.execute("UPDATE bookings SET status = 'done' WHERE reference = 'B-1042'")
    with pytest.raises(Refused, match="Booking B-1042 can't be cancelled now."):
        actions.confirm("C-7", action.id, NOW)
    assert status(db, "B-1042") == "done"
