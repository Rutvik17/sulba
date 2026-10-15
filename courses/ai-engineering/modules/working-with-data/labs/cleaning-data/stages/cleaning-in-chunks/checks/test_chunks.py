import gc
import time

import pandas as pd
import pytest

from cleaning import clean_chunks

PATH = "data/encounters.csv"
# The memory check's chunks: copies of the extract's first rows, each with later encounters of
# the same patients; and how many chunks' rows it allows. The speed check's chunks, copies of
# the whole extract, its seconds, and the chunks it times first, which stop it early when they
# take more than twice their share of the seconds.
HELD_ROWS, HELD_COPIES, HELD = 2000, 6, 3
COPIES, LIMIT, TRIAL = 10, 1.0, 2


@pytest.fixture(scope="module")
def table():
    return pd.read_csv(PATH, na_values=["?"], keep_default_na=False)


def rows_alive(*besides):
    """The rows of every DataFrame alive, but those given."""
    gc.collect()
    frames = [o for o in gc.get_objects() if isinstance(o, pd.DataFrame)]
    return sum(len(o) for o in frames if all(o is not frame for frame in besides))


def copies(rows, count):
    """count copies of rows, each with its encounters moved later."""
    for k in range(count):
        chunk = rows.copy()
        chunk["encounter_id"] += k * 10**9
        yield chunk


def one_patient(table, encounters, discharges):
    """A chunk for each encounter of one patient, made from the extract's first rows."""
    rows = table.iloc[: len(encounters)].copy()
    rows["patient_nbr"] = 1
    rows["encounter_id"] = encounters
    rows["discharge_disposition_id"] = discharges
    return [rows.iloc[[i]] for i in range(len(rows))]


@pytest.mark.id("tst_m0d1nb")
def test_one_chunk_at_a_time(table, record_property):
    """One chunk at a time"""
    rows = table.iloc[:HELD_ROWS]
    baseline, held = rows_alive(rows), []

    def chunks():
        for k, chunk in enumerate(copies(rows, HELD_COPIES)):
            if k == HELD_COPIES - 1:
                held.append(rows_alive(rows, chunk) - baseline)
            yield chunk

    clean_chunks(chunks())
    record_property("note", f"Held {held[0]:,} rows while reading the last chunk.")
    assert held[0] <= HELD * HELD_ROWS


@pytest.mark.id("tst_up4a94")
def test_earliest_in_a_later_chunk(table):
    """A patient's earliest encounter in a later chunk"""
    found = clean_chunks(iter(one_patient(table, [50, 20, 40], [1, 1, 1])))
    assert found["encounter_id"].tolist() == [20]


@pytest.mark.id("tst_9f4h6n")
def test_first_in_hospice(table):
    """A patient whose first encounter ended in hospice care"""
    for encounters in ([30, 10], [10, 30]):
        discharges = [13 if encounter == 10 else 1 for encounter in encounters]
        found = clean_chunks(iter(one_patient(table, encounters, discharges)))
        assert found["encounter_id"].tolist() == [], encounters


@pytest.mark.id("tst_wr3y5h")
def test_fast(table, record_property):
    """Fast"""
    chunks = list(copies(table, COPIES))
    start = time.perf_counter()
    clean_chunks(iter(chunks[:TRIAL]))
    trial = time.perf_counter() - start
    if trial > 2 * LIMIT * TRIAL / COPIES:
        record_property(
            "note",
            f"{trial:.2f} s for {TRIAL} chunks, so about {trial * COPIES / TRIAL:.0f} s for "
            f"{COPIES}.",
        )
        pytest.fail("Too slow.")
    start = time.perf_counter()
    found = clean_chunks(iter(chunks))
    seconds = time.perf_counter() - start
    record_property("note", f"{seconds:.2f} s for {COPIES * len(table):,} encounters.")
    assert seconds < LIMIT
    assert found["encounter_id"].max() < 10**9
