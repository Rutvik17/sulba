import pandas as pd
import pytest

from cleaning import (
    drop_deaths_and_hospice,
    first_encounters,
    mark_unknown,
    read_encounters,
    readmitted_within_30_days,
)

DEATH_OR_HOSPICE = {11, 13, 14, 19, 20, 21}


@pytest.fixture(scope="module")
def table():
    return mark_unknown(read_encounters("data/encounters.csv"))


@pytest.mark.id("tst_wcacbu")
def test_first_encounters(table):
    """Each patient once, at their lowest encounter_id, in order"""
    first = first_encounters(table)
    earliest = table.groupby("patient_nbr")["encounter_id"].min()
    assert sorted(first["encounter_id"]) == sorted(earliest)
    assert first["patient_nbr"].is_unique
    assert first["encounter_id"].is_monotonic_increasing


@pytest.mark.id("tst_di3rsb")
def test_first_in_any_order():
    """The lowest encounter_id, wherever it comes in the table"""
    table = pd.DataFrame(
        {
            "encounter_id": [30, 10, 20, 40],
            "patient_nbr": [7, 7, 8, 7],
            "readmitted": ["NO", "<30", ">30", "NO"],
        }
    )
    assert first_encounters(table)["encounter_id"].tolist() == [10, 20]


@pytest.mark.id("tst_ui6emr")
def test_deaths_and_hospice(table):
    """Every death and hospice discharge left out, and every other encounter kept"""
    kept = drop_deaths_and_hospice(table)
    ending = table["discharge_disposition_id"].isin(DEATH_OR_HOSPICE)
    assert sorted(kept["encounter_id"]) == sorted(table["encounter_id"][~ending])


@pytest.mark.id("tst_xdf6pi")
def test_unknown_discharge_kept():
    """An encounter whose discharge is unknown kept"""
    table = pd.DataFrame(
        {
            "encounter_id": [1, 2, 3, 4],
            "discharge_disposition_id": pd.array([1, None, 11, 13], dtype="Int64"),
        }
    )
    assert drop_deaths_and_hospice(table)["encounter_id"].tolist() == [1, 2]


@pytest.mark.id("tst_dd0z65")
def test_readmitted(table):
    """True only for a readmission within 30 days"""
    soon = readmitted_within_30_days(table)
    assert soon.dtype == bool
    assert soon.tolist() == (table["readmitted"] == "<30").tolist()


@pytest.mark.id("tst_j4lyna")
def test_table_unchanged(table):
    """The table given left as it was"""
    before = table.copy()
    drop_deaths_and_hospice(first_encounters(table))
    readmitted_within_30_days(table)
    pd.testing.assert_frame_equal(table, before)
