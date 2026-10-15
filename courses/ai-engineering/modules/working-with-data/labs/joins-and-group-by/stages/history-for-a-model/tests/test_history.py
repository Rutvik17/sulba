import pandas as pd
import pytest

from report import history, read_mapping

COLUMNS = ["earlier_encounters", "earlier_readmissions", "previous_discharge"]
FIELDS = ["encounter_id", "patient_nbr", "discharge_disposition_id", "readmitted"]


@pytest.fixture(scope="module")
def mapping():
    return read_mapping("data/ids-mapping.csv")


@pytest.fixture(scope="module")
def table():
    return pd.read_csv("data/encounters.csv", na_values=["?"], keep_default_na=False)


@pytest.fixture(scope="module")
def found(table, mapping):
    return history(table, mapping)


def encounters(rows):
    """A small table of encounters, each its id, patient, discharge code and outcome, with the
    other codes 1."""
    table = pd.DataFrame(rows, columns=FIELDS)
    return table.assign(admission_type_id=1, admission_source_id=1)


@pytest.mark.id("tst_vy9q6c")
def test_by_hand(mapping):
    """Two patients' histories worked by hand"""
    table = encounters(
        [
            [10, 1, 1, "<30"],
            [20, 2, 3, "NO"],
            [30, 1, 6, ">30"],
            [40, 1, 1, "NO"],
            [50, 2, 1, "<30"],
        ]
    )
    found = history(table, mapping)
    assert found["earlier_encounters"].tolist() == [0, 0, 1, 2, 1]
    assert found["earlier_readmissions"].tolist() == [0, 0, 1, 1, 0]
    missing = found["previous_discharge"].isna()
    assert missing.tolist() == [True, True, False, False, False]
    assert found["previous_discharge"].iloc[2:].tolist() == [
        "Discharged to home",
        "Discharged/transferred to home with home health service",
        "Discharged/transferred to SNF",
    ]


@pytest.mark.id("tst_zp18pw")
def test_every_encounter(found, table):
    """A row for each encounter, in the table's order, the counts whole numbers"""
    assert found.index.equals(table.index)
    assert list(found.columns) == COLUMNS
    assert pd.api.types.is_integer_dtype(found["earlier_encounters"])
    assert pd.api.types.is_integer_dtype(found["earlier_readmissions"])


@pytest.mark.id("tst_3btpqb")
def test_first_encounters(found, table):
    """Each patient's first encounter without a history, and every other with one"""
    earliest = table.groupby("patient_nbr")["encounter_id"].transform("min")
    first = table["encounter_id"] == earliest
    assert (found.loc[first, "earlier_encounters"] == 0).all()
    assert (found.loc[first, "earlier_readmissions"] == 0).all()
    assert found.loc[first, "previous_discharge"].isna().all()
    assert (found.loc[~first, "earlier_encounters"] > 0).all()
    assert found.loc[~first, "previous_discharge"].notna().all()


@pytest.mark.id("tst_35f1ib")
def test_patients_seen_most(found, table, mapping):
    """The histories of the patients seen most, worked out one encounter at a time"""
    codes = mapping["discharge_disposition_id"]
    discharges = dict(zip(codes["code"], codes["description"], strict=True))
    for patient in table["patient_nbr"].value_counts().index[:20]:
        rows = table[table["patient_nbr"] == patient].sort_values("encounter_id")
        earlier = []
        for label, row in rows.iterrows():
            assert found.loc[label, "earlier_encounters"] == len(earlier)
            readmissions = sum(before["readmitted"] == "<30" for before in earlier)
            assert found.loc[label, "earlier_readmissions"] == readmissions
            if earlier:
                discharge = discharges[earlier[-1]["discharge_disposition_id"]]
                assert found.loc[label, "previous_discharge"] == discharge
            earlier.append(row)


@pytest.mark.id("tst_p0ezzl")
def test_table_unchanged(table, mapping):
    """The table given left as it was"""
    before = table.copy()
    history(table, mapping)
    pd.testing.assert_frame_equal(table, before)
