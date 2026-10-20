import numpy as np
import pytest

from desk import build, search, update
from store import connect, create, load


def unit(*values):
    vector = np.zeros(768, dtype=np.float32)
    vector[: len(values)] = values
    return vector / np.linalg.norm(vector)


ROWS = [
    ("p1", "ssa", "page-a", "Apply for benefits online.", unit(1.0, 0.0)),
    ("p2", "va", "page-b", "Renew your license.", unit(0.0, 1.0)),
    ("p3", "dmv", "page-c", "Pay off your loan.", unit(1.0, 1.0)),
]


def ready(database):
    conn = connect(database)
    create(conn)
    load(conn, ROWS)
    build(conn)
    return conn


@pytest.mark.id("tst_s1bm9x")
def test_search(database):
    """The nearest passages first, in a service or in every one"""
    with ready(database) as conn:
        assert search(conn, unit(1.0, 0.1), 2) == ["p1", "p3"]
        assert search(conn, unit(1.0, 0.1), 2, "va") == ["p2"]


@pytest.mark.id("tst_k9es8x")
def test_update(database):
    """A new passage, and a changed one"""
    with ready(database) as conn:
        update(
            conn,
            [
                ("p1", "ssa", "page-a", "Apply in person.", unit(0.0, 0.0, 1.0)),
                ("p4", "va", "page-d", "Find a clinic.", unit(0.0, 1.0, 1.0)),
            ],
        )
        bodies = dict(conn.execute("SELECT id, body FROM passages").fetchall())
        assert search(conn, unit(0.0, 0.0, 1.0), 1) == ["p1"]
    assert bodies == {
        "p1": "Apply in person.",
        "p2": "Renew your license.",
        "p3": "Pay off your loan.",
        "p4": "Find a clinic.",
    }
