import pandas as pd
import pytest

from checks import drift

# The size of the larger batch in the check of batches of different sizes, in copies.
COPIES = 3


@pytest.fixture(scope="module")
def table():
    return pd.read_csv("data/encounters.csv", na_values=["?"], keep_default_na=False)


def reported(found, column, value):
    """The previous and current shares reported for a column's value, or None."""
    rows = found[(found["column"] == column) & (found["value"] == value)]
    if rows.empty:
        return None
    return round(rows["previous"].iloc[0], 6), round(rows["current"].iloc[0], 6)


@pytest.mark.id("tst_092twp")
def test_new_value(table):
    """A value new this month"""
    previous = table.iloc[:100].copy()
    current = previous.copy()
    current.loc[current.index[:20], "admission_source_id"] = 27
    found = drift(previous, current, 0.05)
    assert reported(found, "admission_source_id", 27) == (0.0, 0.2)


@pytest.mark.id("tst_2gnamu")
def test_gone_value(table):
    """A value gone this month"""
    current = table.iloc[:100].copy()
    previous = current.copy()
    previous.loc[previous.index[:20], "admission_source_id"] = 27
    found = drift(previous, current, 0.05)
    assert reported(found, "admission_source_id", 27) == (0.2, 0.0)


@pytest.mark.id("tst_h1s2aq")
def test_column_going_missing(table):
    """A column going missing"""
    current = table.copy()
    current.loc[current.index[:3000], "race"] = None
    found = drift(table, current, 0.05)
    missing = found[(found["column"] == "race") & found["value"].isna()]
    assert len(missing) == 1
    assert missing["change"].iloc[0] > 0.25


@pytest.mark.id("tst_xz5w8z")
def test_different_sizes(table):
    """Batches of different sizes"""
    bigger = pd.concat([table] * COPIES, ignore_index=True)
    assert drift(table, bigger, 0.01).empty
