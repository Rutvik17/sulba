import csv
import sqlite3

import pandas as pd
import pytest

from queries import describe, load

COLUMNS = ["admission_type_id", "discharge_disposition_id", "admission_source_id"]


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


@pytest.fixture(scope="module")
def connection(table, mapping):
    connection = sqlite3.connect(":memory:")
    load(connection, table, mapping)
    return connection


@pytest.fixture(scope="module")
def described(connection):
    return describe(connection)


@pytest.mark.id("tst_e6xhe5")
def test_every_encounter(described, table):
    """Every encounter once, in order of encounter_id, with its three descriptions"""
    assert described["encounter_id"].tolist() == sorted(table["encounter_id"])
    names = [column.removesuffix("_id") for column in COLUMNS]
    assert list(described.columns) == ["encounter_id", *names]


@pytest.mark.id("tst_qec257")
def test_descriptions(described, table, mapping):
    """Each code's description beside it"""
    ordered = table.sort_values("encounter_id")
    for column in COLUMNS:
        codes = mapping[column]
        words = dict(zip(codes["code"], codes["description"], strict=True))
        expected = [words[code] for code in ordered[column]]
        assert described[column.removesuffix("_id")].tolist() == expected, column


@pytest.mark.id("tst_j45scw")
def test_code_the_mapping_lacks(table, mapping):
    """An encounter whose code the mapping lacks kept, its description missing"""
    connection = sqlite3.connect(":memory:")
    load(connection, table.iloc[:3], mapping)
    connection.execute(
        "INSERT INTO encounters (encounter_id, patient_nbr, admission_type_id, "
        "discharge_disposition_id, admission_source_id) VALUES (1, 1, 1, 1, 27)"
    )
    found = describe(connection)
    assert len(found) == 4
    first = found.iloc[0]
    assert first["encounter_id"] == 1
    assert first["admission_type"] == "Emergency"
    assert pd.isna(first["admission_source"])
