import pandas as pd
import pytest

from validate import validate


@pytest.fixture(scope="module")
def rows():
    """The extract's first rows, which break no rule."""
    table = pd.read_csv("data/encounters.csv", na_values=["?"], keep_default_na=False)
    return table.iloc[:20]


@pytest.mark.id("tst_4tsaqj")
def test_one_wrong_value(rows):
    """One value not allowed among many"""
    batch = rows.copy()
    batch.loc[batch.index[0], "gender"] = "female"
    assert validate(batch) == ["gender: values not allowed"]


@pytest.mark.id("tst_xb52v3")
def test_missing_stay(rows):
    """A missing length of stay"""
    batch = rows.copy()
    batch["time_in_hospital"] = batch["time_in_hospital"].astype(float)
    batch.loc[batch.index[0], "time_in_hospital"] = None
    assert validate(batch) == ["time_in_hospital: out of range"]


@pytest.mark.id("tst_ssw3he")
def test_shared_id(rows):
    """Two different encounters sharing an id"""
    batch = rows.copy()
    batch.loc[batch.index[1], "encounter_id"] = batch["encounter_id"].iloc[0]
    assert validate(batch) == ["encounter_id: repeated"]


@pytest.mark.id("tst_tupuf2")
def test_after_another_death(rows):
    """An encounter after a death the mapping codes 20"""
    batch = rows.iloc[:2].copy()
    batch["patient_nbr"] = 1
    batch["encounter_id"] = [10, 20]
    batch["discharge_disposition_id"] = [20, 1]
    assert validate(batch) == ["encounters after a death"]
