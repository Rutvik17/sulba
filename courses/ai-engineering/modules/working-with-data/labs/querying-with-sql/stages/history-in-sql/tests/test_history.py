import csv
import sqlite3

import pandas as pd
import pytest

from queries import history, load

COLUMNS = [
    "encounter_id",
    "earlier_encounters",
    "earlier_readmissions",
    "previous_discharge",
]
FIELDS = ["encounter_id", "patient_nbr", "discharge_disposition_id", "readmitted"]


def read_mapping(path):
    """The mapping's tables by the column each describes, each of code and description."""
    tables, current = {}, None
    with open(path, newline="") as file:
        for row in csv.reader(file):
            if not any(row):
                current = None
            elif current is None:
                current = tables.setdefault(row[0], [])
            else:
                current.append((int(row[0]), row[1].strip()))
    columns = ["code", "description"]
    return {name: pd.DataFrame(rows, columns=columns) for name, rows in tables.items()}


@pytest.fixture(scope="module")
def table():
    return pd.read_csv("data/encounters.csv", na_values=["?"], keep_default_na=False)


@pytest.fixture(scope="module")
def mapping():
    return read_mapping("data/ids-mapping.csv")


def database(table, mapping):
    connection = sqlite3.connect(":memory:")
    load(connection, table, mapping)
    return connection


@pytest.fixture(scope="module")
def found(table, mapping):
    return history(database(table, mapping))


@pytest.mark.id("tst_xhn9zt")
def test_by_hand(mapping):
    """Two patients' histories worked by hand"""
    rows = [
        [10, 1, 1, "<30"],
        [20, 2, 3, "NO"],
        [30, 1, 6, ">30"],
        [40, 1, 1, "NO"],
        [50, 2, 1, "<30"],
    ]
    found = history(database(pd.DataFrame(rows, columns=FIELDS), mapping))
    assert found["encounter_id"].tolist() == [10, 20, 30, 40, 50]
    assert found["earlier_encounters"].tolist() == [0, 0, 1, 2, 1]
    assert found["earlier_readmissions"].tolist() == [0, 0, 1, 1, 0]
    missing = found["previous_discharge"].isna()
    assert missing.tolist() == [True, True, False, False, False]
    assert found["previous_discharge"].iloc[2:].tolist() == [
        "Discharged to home",
        "Discharged/transferred to home with home health service",
        "Discharged/transferred to SNF",
    ]


@pytest.mark.id("tst_ij12qz")
def test_every_encounter(found, table):
    """Every encounter once, in order of encounter_id, the counts whole numbers"""
    assert list(found.columns) == COLUMNS
    assert found["encounter_id"].tolist() == sorted(table["encounter_id"])
    assert pd.api.types.is_integer_dtype(found["earlier_encounters"])
    assert pd.api.types.is_integer_dtype(found["earlier_readmissions"])


@pytest.mark.id("tst_o77x1u")
def test_patients_seen_most(found, table, mapping):
    """The histories of the patients seen most, worked out one encounter at a time"""
    codes = mapping["discharge_disposition_id"]
    discharges = dict(zip(codes["code"], codes["description"], strict=True))
    by_id = found.set_index("encounter_id")
    for patient in table["patient_nbr"].value_counts().index[:20]:
        rows = table[table["patient_nbr"] == patient].sort_values("encounter_id")
        earlier = []
        for row in rows.itertuples():
            got = by_id.loc[row.encounter_id]
            assert got["earlier_encounters"] == len(earlier)
            readmissions = sum(before.readmitted == "<30" for before in earlier)
            assert got["earlier_readmissions"] == readmissions
            if earlier:
                discharge = discharges[earlier[-1].discharge_disposition_id]
                assert got["previous_discharge"] == discharge
            earlier.append(row)


@pytest.mark.id("tst_udjcw6")
def test_first_encounters(found, table):
    """Each patient's first encounter without a history, and every other with one"""
    first = found["encounter_id"].isin(
        table.groupby("patient_nbr")["encounter_id"].min()
    )
    assert (found.loc[first, "earlier_encounters"] == 0).all()
    assert (found.loc[first, "earlier_readmissions"] == 0).all()
    assert found.loc[first, "previous_discharge"].isna().all()
    assert (found.loc[~first, "earlier_encounters"] > 0).all()
