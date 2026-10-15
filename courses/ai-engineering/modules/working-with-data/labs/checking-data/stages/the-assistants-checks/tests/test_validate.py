import pandas as pd
import pytest

from validate import validate


@pytest.fixture(scope="module")
def table():
    return pd.read_csv("data/encounters.csv", na_values=["?"], keep_default_na=False)


@pytest.mark.id("tst_lvlols")
def test_extract(table):
    """The extract's only problem: its encounters after a death"""
    assert validate(table) == ["encounters after a death"]


@pytest.mark.id("tst_ilttsv")
def test_wrong_genders(table):
    """An extract with every gender wrong stopped"""
    rows = table.iloc[:20].assign(gender="X")
    assert validate(rows) == ["gender: values not allowed"]


@pytest.mark.id("tst_dw7o4x")
def test_stay_out_of_range(table):
    """A stay out of range stopped"""
    rows = table.iloc[:20].copy()
    rows.loc[rows.index[0], "time_in_hospital"] = 15
    assert validate(rows) == ["time_in_hospital: out of range"]


@pytest.mark.id("tst_amzcn6")
def test_repeated_row(table):
    """A row sent twice stopped"""
    rows = pd.concat([table.iloc[:20], table.iloc[[0]]])
    assert validate(rows) == ["encounter_id: repeated"]
