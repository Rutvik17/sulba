import random

import pytest

from bookings import Calendar

BOOKINGS = 50_000


@pytest.mark.id("tst_1eaka5")
def test_book():
    """Adds a booking that fits and refuses one that overlaps"""
    calendar = Calendar()
    assert calendar.book(10, 20) is True
    assert calendar.book(15, 25) is False
    assert calendar.book(20, 30) is True


@pytest.mark.id("tst_4s4ni1")
def test_edges():
    """Refuses a booking inside, around or the same as one, and takes one that ends where another starts"""
    calendar = Calendar()
    assert calendar.book(10, 20) is True
    assert calendar.book(12, 18) is False
    assert calendar.book(5, 25) is False
    assert calendar.book(10, 20) is False
    assert calendar.book(5, 10) is True
    assert calendar.book(4, 6) is False


@pytest.mark.id("tst_hp2j9s")
def test_random():
    """Matches comparing every booking so far, on random bookings"""
    rng = random.Random(531)
    for _ in range(200):
        calendar, booked = Calendar(), []
        for _ in range(rng.randint(0, 15)):
            start = rng.randint(0, 40)
            end = start + rng.randint(1, 6)
            fits = all(
                end <= other_start or other_end <= start
                for other_start, other_end in booked
            )
            assert calendar.book(start, end) is fits
            if fits:
                booked.append((start, end))


@pytest.mark.id("tst_vqt0s0")
def test_long():
    """Takes many bookings in time"""
    rng = random.Random(532)
    calendar = Calendar()
    slots = list(range(BOOKINGS))
    rng.shuffle(slots)
    for slot in slots:
        assert calendar.book(10 * slot, 10 * slot + 10) is True
    for _ in range(BOOKINGS):
        start = rng.randrange(10 * BOOKINGS)
        assert calendar.book(start, start + 1) is False
