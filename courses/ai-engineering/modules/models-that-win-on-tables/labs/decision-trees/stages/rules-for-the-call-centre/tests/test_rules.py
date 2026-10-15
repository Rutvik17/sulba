import numpy as np
import pytest

from tree import rules

COLUMNS = ["age", ("job", "admin."), ("job", "retired"), "pdays"]


def plain(found):
    """Each rule as (conditions, calls, yes), its conditions in plain tuples."""
    out = []
    for rule in found:
        conditions = {}
        for name, (first, second) in rule["conditions"].items():
            if isinstance(first, str):
                second = second if isinstance(second, str) else tuple(sorted(second))
                conditions[name] = (first, second)
            else:
                conditions[name] = (float(first), float(second))
        out.append((conditions, int(rule["calls"]), int(rule["yes"])))
    return out


def leaf(calls, yes):
    return {"calls": calls, "yes": yes}


def split(column, threshold, left, right):
    calls, yes = left["calls"] + right["calls"], left["yes"] + right["yes"]
    return {**leaf(calls, yes), "column": column, "threshold": threshold} | {
        "left": left,
        "right": right,
    }


@pytest.mark.id("tst_2vc19a")
def test_by_hand():
    """A tree's rules worked by hand, the likeliest first"""
    tree = split(0, 60.5, split(1, 0.5, leaf(50, 12), leaf(30, 6)), leaf(20, 10))
    assert plain(rules(tree, COLUMNS)) == [
        ({"age": (60.5, np.inf)}, 20, 10),
        ({"age": (-np.inf, 60.5), "job": ("is not", ("admin.",))}, 50, 12),
        ({"age": (-np.inf, 60.5), "job": ("is", "admin.")}, 30, 6),
    ]


@pytest.mark.id("tst_lddjnc")
def test_ranges():
    """Splits on one number column merged into one range"""
    inner = split(3, 10.5, leaf(2, 2), leaf(2, 1))
    tree = split(0, 60.5, split(0, 30.5, leaf(3, 0), inner), leaf(3, 2))
    assert plain(rules(tree, COLUMNS)) == [
        ({"age": (30.5, 60.5), "pdays": (-np.inf, 10.5)}, 2, 2),
        ({"age": (60.5, np.inf)}, 3, 2),
        ({"age": (30.5, 60.5), "pdays": (10.5, np.inf)}, 2, 1),
        ({"age": (-np.inf, 30.5)}, 3, 0),
    ]


@pytest.mark.id("tst_zsnf8f")
def test_categories():
    """Categories ruled out together, and one a call is in"""
    tree = split(2, 0.5, split(1, 0.5, leaf(6, 1), leaf(4, 2)), leaf(5, 4))
    assert plain(rules(tree, COLUMNS)) == [
        ({"job": ("is", "retired")}, 5, 4),
        ({"job": ("is", "admin.")}, 4, 2),
        ({"job": ("is not", ("admin.", "retired"))}, 6, 1),
    ]


@pytest.mark.id("tst_3bqpn6")
def test_order():
    """A tree of one leaf, and equal shares in the tree's order"""
    assert plain(rules(leaf(5, 2), COLUMNS)) == [({}, 5, 2)]
    tree = split(0, 40.5, leaf(4, 2), leaf(2, 1))
    assert plain(rules(tree, COLUMNS)) == [
        ({"age": (-np.inf, 40.5)}, 4, 2),
        ({"age": (40.5, np.inf)}, 2, 1),
    ]
