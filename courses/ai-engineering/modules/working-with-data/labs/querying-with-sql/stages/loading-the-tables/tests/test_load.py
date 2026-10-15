import csv
import sqlite3

import pandas as pd
import pytest

from queries import load

ENCOUNTERS, MAPPING = "data/encounters.csv", "data/ids-mapping.csv"


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
    return pd.read_csv(ENCOUNTERS, na_values=["?"], keep_default_na=False)


@pytest.fixture(scope="module")
def mapping():
    return read_mapping(MAPPING)


@pytest.fixture(scope="module")
def connection(table, mapping):
    connection = sqlite3.connect(":memory:")
    load(connection, table, mapping)
    return connection


@pytest.mark.id("tst_yjfe4h")
def test_encounters(connection, table):
    """Every encounter, with the extract's columns"""
    columns = [row[1] for row in connection.execute("PRAGMA table_info(encounters)")]
    assert columns == list(table.columns)
    (count,) = connection.execute("SELECT COUNT(*) FROM encounters").fetchone()
    assert count == len(table)


@pytest.mark.id("tst_w569pu")
def test_missing_as_null(connection, table):
    """A missing value as NULL"""
    found = connection.execute(
        "SELECT COUNT(*) FROM encounters WHERE medical_specialty IS NULL"
    ).fetchone()
    assert found == (table["medical_specialty"].isna().sum(),)


@pytest.mark.id("tst_3h5hym")
def test_codes(connection, mapping):
    """A row for each code of each code column, the codes whole numbers"""
    rows = connection.execute(
        "SELECT column_name, code, description FROM codes"
    ).fetchall()
    expected = [
        (name, code, text)
        for name, codes in mapping.items()
        for code, text in zip(codes["code"], codes["description"], strict=True)
    ]
    assert sorted(rows) == sorted(expected)
    types = connection.execute("SELECT DISTINCT typeof(code) FROM codes").fetchall()
    assert types == [("integer",)]


@pytest.mark.id("tst_ic3okf")
def test_code_twice(table, mapping):
    """A code listed twice refused"""
    connection = sqlite3.connect(":memory:")
    load(connection, table.iloc[:5], mapping)
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            "INSERT INTO codes VALUES ('admission_type_id', 1, 'Emergency')"
        )


@pytest.mark.id("tst_l65l8h")
def test_quote(table):
    """A description with a quote in it kept as written"""
    connection = sqlite3.connect(":memory:")
    codes = pd.DataFrame({"code": [1], "description": ["St Mary's referral"]})
    load(connection, table.iloc[:5], {"admission_source_id": codes})
    found = connection.execute("SELECT description FROM codes").fetchall()
    assert found == [("St Mary's referral",)]


@pytest.mark.id("tst_yb3v9w")
def test_kept(tmp_path, table, mapping):
    """Kept in a database file once its connection closes"""
    path = tmp_path / "hospital.db"
    connection = sqlite3.connect(path)
    load(connection, table, mapping)
    connection.close()
    reopened = sqlite3.connect(path)
    codes = sum(len(rows) for rows in mapping.values())
    (count,) = reopened.execute("SELECT COUNT(*) FROM encounters").fetchone()
    assert count == len(table)
    assert reopened.execute("SELECT COUNT(*) FROM codes").fetchone() == (codes,)
