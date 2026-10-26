import random

import pytest
from route import cheapest

CITIES = 1_000
EXTRA = 20_000
STOPS = 30


def every_route(cities, flights, source, target, stops):
    """The lowest fare, by trying every route of at most stops + 1 flights."""
    best = -1
    waiting = [(source, 0, 0)]
    while waiting:
        city, fare, taken = waiting.pop()
        if city == target and taken > 0 and (best == -1 or fare < best):
            best = fare
        if taken <= stops:
            for start, end, price in flights:
                if start == city:
                    waiting.append((end, fare + price, taken + 1))
    return best


@pytest.mark.id("tst_9wy4jv")
def test_cheapest():
    """Gives the lowest fare within the stops"""
    flights = [(0, 1, 100), (1, 2, 100), (2, 3, 100), (0, 2, 500), (1, 3, 600)]
    assert cheapest(4, flights, 0, 3, 2) == 300
    assert cheapest(4, flights, 0, 3, 1) == 600
    assert cheapest(4, flights, 0, 3, 0) == -1


@pytest.mark.id("tst_ponqs8")
def test_edges():
    """Takes a direct flight with no stops, counts flights of fare 0, and gives -1 with no
    route"""
    assert cheapest(2, [(0, 1, 7)], 0, 1, 0) == 7
    assert cheapest(3, [(0, 1, 0), (1, 2, 0)], 0, 2, 1) == 0
    assert cheapest(3, [(1, 2, 5)], 0, 2, 5) == -1
    assert cheapest(3, [(0, 1, 1), (1, 0, 1), (1, 2, 1)], 0, 2, 1) == 2


@pytest.mark.id("tst_96vn5d")
def test_random():
    """Matches trying every route, on random airlines"""
    rng = random.Random(209)
    for _ in range(300):
        cities = rng.randint(2, 6)
        flights = [
            (rng.randrange(cities), rng.randrange(cities), rng.randint(0, 20))
            for _ in range(rng.randint(0, 10))
        ]
        source, target = rng.sample(range(cities), 2)
        stops = rng.randint(0, 3)
        assert cheapest(cities, flights, source, target, stops) == every_route(
            cities, flights, source, target, stops
        )


@pytest.mark.id("tst_zs6n8n")
def test_long():
    """Finds the cheapest route within the stops on a large airline in time"""
    rng = random.Random(210)
    # A fare of 1 along every city, too many stops, and a way through city 500 with 1 stop.
    chain = [(city, city + 1, 1) for city in range(CITIES - 1)]
    short = [(0, 500, 10_000), (500, CITIES - 1, 10_000)]
    extra = [
        (
            rng.randrange(CITIES),
            rng.randrange(CITIES),
            rng.randint(1_000_000, 2_000_000),
        )
        for _ in range(EXTRA)
    ]
    flights = chain + short + extra
    rng.shuffle(flights)
    assert cheapest(CITIES, flights, 0, CITIES - 1, STOPS) == 20_000
    assert cheapest(CITIES, flights, 0, STOPS + 1, STOPS) == STOPS + 1
