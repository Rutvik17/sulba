import pandas as pd
import pytest

from checks import encounter_problems

FIELDS = ["encounter_id", "patient_nbr", "discharge_disposition_id", "age", "gender"]


@pytest.fixture(scope="module")
def table():
    return pd.read_csv("data/encounters.csv", na_values=["?"], keep_default_na=False)


def rows_of(found):
    return list(found.itertuples(index=False, name=None))


@pytest.mark.id("tst_92ke6m")
def test_by_hand():
    """Five patients' encounters worked by hand"""
    table = pd.DataFrame(
        [
            [10, 1, 11, "[70-80)", "Female"],
            [20, 1, 1, "[70-80)", "Female"],
            [30, 2, 1, "[50-60)", "Male"],
            [40, 2, 1, "[40-50)", "Male"],
            [50, 3, 1, "[60-70)", "Female"],
            [60, 3, 1, "[60-70)", "Male"],
            [70, 4, 20, "[80-90)", "Male"],
            [80, 4, 1, "[70-80)", "Female"],
            [90, 5, 1, "[30-40)", "Male"],
        ],
        columns=FIELDS,
    )
    found = encounter_problems(table)
    assert list(found.columns) == ["encounter_id", "patient_nbr", "problem"]
    assert rows_of(found) == [
        (20, 1, "after a death"),
        (40, 2, "younger"),
        (60, 3, "gender changed"),
        (80, 4, "after a death"),
        (80, 4, "younger"),
        (80, 4, "gender changed"),
    ]


@pytest.mark.id("tst_1pc795")
def test_extract(table):
    """The extract's encounters after a death and in a younger age group"""
    assert rows_of(encounter_problems(table)) == [
        (351954356, 43466490, "younger"),
        (353165312, 89400798, "after a death"),
        (378480020, 100581894, "after a death"),
        (384884366, 42491844, "younger"),
        (392571404, 100581894, "after a death"),
    ]


@pytest.mark.id("tst_d0a2j8")
def test_any_order(table):
    """The same problems whatever order the rows come in"""
    shuffled = table.sample(frac=1, random_state=0)
    found = encounter_problems(shuffled)
    pd.testing.assert_frame_equal(found, encounter_problems(table))


@pytest.mark.id("tst_vtzvn7")
def test_table_unchanged(table):
    """The table given left as it was"""
    before = table.copy()
    encounter_problems(table)
    pd.testing.assert_frame_equal(table, before)
