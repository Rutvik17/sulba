import csv
import sqlite3
import time

import pandas as pd
import pytest

from queries import history, load

FIELDS = ["encounter_id", "patient_nbr", "discharge_disposition_id", "readmitted"]
# The speed check's copies of the extract, each of other patients, and its seconds.
COPIES, LIMIT = 10, 2.0


def read_mapping(path):
    """The mapping's tables by the column each describes, each of code and description."""
    tables, current = {}, None
    with open(path, newline="") as file:
        for row in csv.reader(file):
            if not any(row):
                current = None
            elif current is None:
                current = tables.setdefault(row[0], [])
            else:
                current.append((int(row[0]), row[1].strip()))
    columns = ["code", "description"]
    return {name: pd.DataFrame(rows, columns=columns) for name, rows in tables.items()}


@pytest.fixture(scope="module")
def table():
    return pd.read_csv("data/encounters.csv", na_values=["?"], keep_default_na=False)


@pytest.fixture(scope="module")
def mapping():
    return read_mapping("data/ids-mapping.csv")


def database(table, mapping):
    connection = sqlite3.connect(":memory:")
    load(connection, table, mapping)
    return connection


@pytest.mark.id("tst_007kt0")
def test_any_order(table, mapping):
    """Encounters stored in any order"""
    expected = history(database(table[FIELDS], mapping))
    shuffled = table[FIELDS].sample(frac=1, random_state=0)
    pd.testing.assert_frame_equal(history(database(shuffled, mapping)), expected)


@pytest.mark.id("tst_rk33uo")
def test_discharge_the_mapping_lacks(mapping):
    """A discharge the mapping lacks"""
    rows = pd.DataFrame([[10, 1, 99, "NO"], [20, 1, 1, "NO"]], columns=FIELDS)
    found = history(database(rows, mapping))
    assert found["encounter_id"].tolist() == [10, 20]
    assert found["earlier_encounters"].tolist() == [0, 1]
    assert found["previous_discharge"].isna().all()


@pytest.mark.id("tst_ykbake")
def test_fast(table, mapping, record_property):
    """Fast"""
    copies = []
    for k in range(COPIES):
        copy = table[FIELDS].copy()
        copy["encounter_id"] += k * 10**9
        copy["patient_nbr"] += k * 10**9
        copies.append(copy)
    one = database(copies[0], mapping)
    start = time.perf_counter()
    history(one)
    trial = time.perf_counter() - start
    if trial > 2 * LIMIT / COPIES:
        record_property(
            "note",
            f"{trial:.2f} s for {len(table):,} encounters, so about {trial * COPIES:.0f} s for "
            f"{COPIES * len(table):,}.",
        )
        pytest.fail("Too slow.")
    connection = database(pd.concat(copies, ignore_index=True), mapping)
    start = time.perf_counter()
    found = history(connection)
    seconds = time.perf_counter() - start
    record_property("note", f"{seconds:.2f} s for {len(found):,} encounters.")
    assert seconds < LIMIT
    assert len(found) == COPIES * len(table)
