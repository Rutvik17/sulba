import pandas as pd
import pytest

from report import readmission_rates


@pytest.fixture(scope="module")
def patients():
    """Each patient's first encounter, without those that ended in death or hospice care."""
    table = pd.read_csv("data/encounters.csv", na_values=["?"], keep_default_na=False)
    first = table.sort_values("encounter_id").drop_duplicates("patient_nbr")
    return first[~first["discharge_disposition_id"].isin([11, 13, 14, 19, 20, 21])]


@pytest.mark.id("tst_reylub")
def test_by_hand():
    """Encounters, readmissions and shares worked by hand, the highest share first"""
    table = pd.DataFrame(
        {
            "group": ["a", "b", "a", "c", "c", "c"],
            "readmitted": ["<30", "<30", ">30", "NO", "<30", "NO"],
        }
    )
    rates = readmission_rates(table, "group", 1)
    assert rates.index.tolist() == ["b", "a", "c"]
    assert rates["encounters"].tolist() == [1, 2, 3]
    assert rates["readmitted"].tolist() == [1, 1, 1]
    assert rates["share"].tolist() == pytest.approx([1, 1 / 2, 1 / 3])


@pytest.mark.id("tst_av1h3q")
def test_missing_group(patients):
    """A missing value counted as a group of its own"""
    rates = readmission_rates(patients, "medical_specialty", 1)
    assert rates["encounters"].sum() == len(patients)
    missing = rates[rates.index.isna()]
    assert missing["encounters"].tolist() == [
        patients["medical_specialty"].isna().sum()
    ]


@pytest.mark.id("tst_qy3kcu")
def test_smallest(patients):
    """Values with fewer encounters than smallest left out"""
    sizes = patients["admission_source_id"].value_counts()
    rates = readmission_rates(patients, "admission_source_id", 30)
    assert sorted(rates.index) == sorted(sizes[sizes >= 30].index)


@pytest.mark.id("tst_vxaser")
def test_discharges(patients):
    """The patients' rates by discharge, the highest share first"""
    rates = readmission_rates(patients, "discharge_disposition_id", 30)
    soon = patients["readmitted"] == "<30"
    for code, row in rates.iterrows():
        group = soon[patients["discharge_disposition_id"] == code]
        assert row["encounters"] == len(group)
        assert row["readmitted"] == group.sum()
        assert row["share"] == pytest.approx(group.mean())
    assert rates["share"].is_monotonic_decreasing


@pytest.mark.id("tst_dwtoln")
def test_table_unchanged(patients):
    """The table given left as it was"""
    before = patients.copy()
    readmission_rates(patients, "age", 1)
    pd.testing.assert_frame_equal(patients, before)
