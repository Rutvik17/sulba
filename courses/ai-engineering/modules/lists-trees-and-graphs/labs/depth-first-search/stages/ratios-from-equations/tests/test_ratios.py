import math
import random

import pytest

from ratios import ratios

VARIABLES = 100_000
QUERIES = 100_000


def close(found, expected):
    return all(
        (a is None and b is None)
        or (a is not None and b is not None and math.isclose(a, b, rel_tol=1e-9))
        for a, b in zip(found, expected, strict=True)
    )


@pytest.mark.id("tst_zt0vqi")
def test_ratios():
    """Answers queries from the equations"""
    equations = [("a", "b", 2.0), ("b", "c", 3.0)]
    queries = [("a", "c"), ("b", "a"), ("a", "e"), ("a", "a"), ("x", "x")]
    assert close(ratios(equations, queries), [6.0, 0.5, None, 1.0, None])


@pytest.mark.id("tst_eckdxj")
def test_edges():
    """Handles no equations, separate groups, and an equation given both ways"""
    assert ratios([], [("a", "b")]) == [None]
    equations = [("a", "b", 4.0), ("c", "d", 5.0), ("b", "a", 0.25)]
    assert close(
        ratios(equations, [("a", "b"), ("d", "c"), ("a", "c")]), [4.0, 0.2, None]
    )


@pytest.mark.id("tst_a3an33")
def test_random():
    """Matches the values the equations came from, on random equations"""
    rng = random.Random(751)
    for _ in range(200):
        names = [f"v{n}" for n in range(rng.randint(1, 8))]
        values = {name: rng.uniform(0.5, 4) for name in names}
        group = {name: name for name in names}

        def root(name):
            while group[name] != name:
                name = group[name]
            return name

        equations = []
        for _ in range(rng.randint(0, 8)):
            top, bottom = rng.choice(names), rng.choice(names)
            equations.append((top, bottom, values[top] / values[bottom]))
            group[root(top)] = root(bottom)
        queries = [
            (rng.choice(names + ["z"]), rng.choice(names + ["z"])) for _ in range(8)
        ]
        known = {name for top, bottom, _ in equations for name in (top, bottom)}
        expected = [
            values[top] / values[bottom]
            if top in known and bottom in known and root(top) == root(bottom)
            else None
            for top, bottom in queries
        ]
        assert close(ratios(equations, queries), expected)


@pytest.mark.id("tst_vtkc7l")
def test_long():
    """Answers many queries along a long chain of equations in time"""
    rng = random.Random(752)
    # Values that alternate 1 and 2 along the chain.
    equations = [
        (f"v{n}", f"v{n + 1}", 0.5 if n % 2 == 0 else 2.0) for n in range(VARIABLES - 1)
    ]
    places = [
        (rng.randrange(VARIABLES), rng.randrange(VARIABLES)) for _ in range(QUERIES)
    ]
    found = ratios(equations, [(f"v{top}", f"v{bottom}") for top, bottom in places])
    assert close(found, [(1 + top % 2) / (1 + bottom % 2) for top, bottom in places])
