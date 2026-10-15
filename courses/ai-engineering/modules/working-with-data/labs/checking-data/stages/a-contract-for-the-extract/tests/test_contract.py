import pandas as pd
import pytest

from checks import contract_problems


@pytest.fixture(scope="module")
def table():
    return pd.read_csv("data/encounters.csv", na_values=["?"], keep_default_na=False)


@pytest.mark.id("tst_9w78i9")
def test_extract(table):
    """The extract keeps the contract"""
    assert contract_problems(table) == []


@pytest.mark.id("tst_m6el7a")
def test_not_allowed(table):
    """Values the contract doesn't allow, counted"""
    rows = table.iloc[:4].copy()
    rows["gender"] = ["Female", "female", "M", "Male"]
    assert contract_problems(rows) == [("gender", "not allowed", 2)]


@pytest.mark.id("tst_ixkti8")
def test_out_of_range(table):
    """Values out of range, counted"""
    rows = table.iloc[:4].copy()
    rows["time_in_hospital"] = [0, 1, 14, 15]
    rows["num_medications"] = [0, 3, 2, 1]
    assert contract_problems(rows) == [
        ("time_in_hospital", "out of range", 2),
        ("num_medications", "out of range", 1),
    ]


@pytest.mark.id("tst_wra5fh")
def test_not_a_number(table):
    """A value that isn't a number counted as out of range"""
    rows = table.iloc[:4].copy()
    rows["time_in_hospital"] = [3, "three", 2, 1]
    assert contract_problems(rows) == [("time_in_hospital", "out of range", 1)]


@pytest.mark.id("tst_uey3fm")
def test_missing(table):
    """Values missing where none may be, counted only as missing"""
    rows = table.iloc[:4].copy()
    rows["race"] = None
    rows["time_in_hospital"] = [3, None, 2, 1]
    rows["readmitted"] = ["NO", None, None, "<30"]
    assert contract_problems(rows) == [
        ("time_in_hospital", "missing", 1),
        ("readmitted", "missing", 2),
    ]


@pytest.mark.id("tst_koahd3")
def test_absent(table):
    """A column the table lacks"""
    rows = table.drop(columns=["readmitted"])
    assert contract_problems(rows) == [("readmitted", "absent", len(rows))]


@pytest.mark.id("tst_f1jfi3")
def test_table_unchanged(table):
    """The table given left as it was"""
    before = table.copy()
    contract_problems(table)
    pd.testing.assert_frame_equal(table, before)
