import time

import pandas as pd
import pytest

from report import history, read_mapping

ENCOUNTERS, MAPPING = "data/encounters.csv", "data/ids-mapping.csv"
# The speed check's copies of the extract, each of other patients, and its seconds.
COPIES, LIMIT = 10, 1.0


@pytest.fixture(scope="module")
def mapping():
    return read_mapping(MAPPING)


@pytest.fixture(scope="module")
def table():
    return pd.read_csv(ENCOUNTERS, na_values=["?"], keep_default_na=False)


@pytest.mark.id("tst_p1gq6s")
def test_any_order(table, mapping):
    """Encounters in any order"""
    expected = history(table, mapping).set_axis(table["encounter_id"])
    shuffled = table.sample(frac=1, random_state=0).reset_index(drop=True)
    found = (
        history(shuffled, mapping)
        .reindex(shuffled.index)
        .set_axis(shuffled["encounter_id"])
    )
    pd.testing.assert_frame_equal(found, expected.loc[shuffled["encounter_id"]])


@pytest.mark.id("tst_ou05my")
def test_table_index(table, mapping):
    """The table's index"""
    rows = table.sample(frac=0.5, random_state=1)
    assert history(rows, mapping).index.equals(rows.index)


@pytest.mark.id("tst_piwf6d")
def test_discharge_the_mapping_lacks(table, mapping):
    """A discharge the mapping lacks"""
    rows = table.iloc[:2].copy()
    rows["patient_nbr"] = 1
    rows["encounter_id"] = [10, 20]
    rows["discharge_disposition_id"] = [99, 1]
    found = history(rows, mapping)
    assert found.index.equals(rows.index)
    assert found["earlier_encounters"].tolist() == [0, 1]
    assert found["previous_discharge"].isna().all()


@pytest.mark.id("tst_iwr5jc")
def test_fast(table, mapping, record_property):
    """Fast"""
    copies = []
    for k in range(COPIES):
        copy = table.copy()
        copy["encounter_id"] += k * 10**9
        copy["patient_nbr"] += k * 10**9
        copies.append(copy)
    start = time.perf_counter()
    history(copies[0], mapping)
    trial = time.perf_counter() - start
    if trial > 2 * LIMIT / COPIES:
        record_property(
            "note",
            f"{trial:.2f} s for {len(table):,} encounters, so about {trial * COPIES:.0f} s for "
            f"{COPIES * len(table):,}.",
        )
        pytest.fail("Too slow.")
    big = pd.concat(copies, ignore_index=True)
    start = time.perf_counter()
    found = history(big, mapping)
    seconds = time.perf_counter() - start
    record_property("note", f"{seconds:.2f} s for {len(big):,} encounters.")
    assert seconds < LIMIT
    assert len(found) == len(big)
