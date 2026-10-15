import pandas as pd
import pytest

from checks import WATCHED, drift

COLUMNS = ["column", "value", "previous", "current", "change"]


@pytest.fixture(scope="module")
def table():
    return pd.read_csv("data/encounters.csv", na_values=["?"], keep_default_na=False)


def rows_of(found):
    return [
        (column, value, round(previous, 6), round(current, 6), round(change, 6))
        for column, value, previous, current, change in found.itertuples(index=False)
    ]


@pytest.mark.id("tst_mhpwul")
def test_by_hand(table):
    """Shares and changes worked by hand, the largest change first"""
    previous = table.iloc[:10].copy()
    previous["readmitted"] = ["NO"] * 4 + ["<30"] * 3 + [">30"] * 3
    current = previous.copy()
    current["readmitted"] = ["NO"] * 7 + ["<30"] * 2 + [">30"]
    found = drift(previous, current, 0.15)
    assert list(found.columns) == COLUMNS
    assert rows_of(found) == [
        ("readmitted", "NO", 0.4, 0.7, 0.3),
        ("readmitted", ">30", 0.3, 0.1, -0.2),
    ]


@pytest.mark.id("tst_22p0bu")
def test_same_extract(table):
    """Nothing reported for the same extract twice"""
    found = drift(table, table, 0)
    assert list(found.columns) == COLUMNS
    assert found.empty


@pytest.mark.id("tst_sgvyvs")
def test_earlier_and_later(table):
    """The extract's earlier and later halves, worked out value by value"""
    ordered = table.sort_values("encounter_id")
    half = len(ordered) // 2
    earlier, later = ordered.iloc[:half], ordered.iloc[half:]
    expected = []
    for column in WATCHED:
        for value in set(earlier[column].dropna()) | set(later[column].dropna()):
            before = (earlier[column] == value).mean()
            after = (later[column] == value).mean()
            if abs(after - before) > 0.05:
                expected.append((column, value, before, after, after - before))
    found = drift(earlier, later, 0.05)
    assert sorted(rows_of(found)) == sorted(
        (c, v, round(b, 6), round(a, 6), round(d, 6)) for c, v, b, a, d in expected
    )
    assert found["change"].abs().is_monotonic_decreasing


@pytest.mark.id("tst_g4tnay")
def test_tables_unchanged(table):
    """The tables given left as they were"""
    earlier, later = table.iloc[:5000].copy(), table.iloc[5000:].copy()
    drift(earlier, later, 0.05)
    pd.testing.assert_frame_equal(earlier, table.iloc[:5000])
    pd.testing.assert_frame_equal(later, table.iloc[5000:])
