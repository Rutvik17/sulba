import csv
import sqlite3

import pandas as pd
import pytest

from dashboard import report


def database(table, opted_out):
    """A database of the encounters given, the mapping's codes and the patients opted out."""
    connection = sqlite3.connect(":memory:")
    table.to_sql("encounters", connection, index=False)
    connection.execute(
        "CREATE TABLE codes (column_name TEXT, code INTEGER, description TEXT)"
    )
    current = None
    with open("data/ids-mapping.csv", newline="") as file:
        for row in csv.reader(file):
            if not any(row):
                current = None
            elif current is None:
                current = row[0]
            else:
                code = (current, int(row[0]), row[1].strip())
                connection.execute("INSERT INTO codes VALUES (?, ?, ?)", code)
    connection.execute("CREATE TABLE opted_out (patient_nbr INTEGER)")
    connection.executemany(
        "INSERT INTO opted_out VALUES (?)", [(p,) for p in opted_out]
    )
    return connection


def small(encounters, opted_out=()):
    """A database of the encounters given, each its id, patient, admission source and outcome,
    discharged home."""
    columns = ["encounter_id", "patient_nbr", "admission_source_id", "readmitted"]
    table = pd.DataFrame(encounters, columns=columns).assign(discharge_disposition_id=1)
    return database(table, opted_out)


@pytest.fixture(scope="module")
def rows():
    table = pd.read_csv("data/encounters.csv", na_values=["?"], keep_default_na=False)
    return report(database(table, []))


@pytest.mark.id("tst_ae343s")
def test_source_shares(rows):
    """Each source's share is its patients readmitted over its patients"""
    sources = rows.drop(index="All sources")
    expected = sources["readmitted"] / sources["patients"]
    assert sources["share"].tolist() == pytest.approx(expected.tolist())


@pytest.mark.id("tst_mqhyb3")
def test_source_the_mapping_lacks():
    """Every patient counted, one from a source the mapping lacks under Unknown"""
    found = report(small([[1, 1, 7, "NO"], [2, 2, 27, "<30"]]))
    assert found.loc["All sources", "patients"] == 2
    assert found.loc["Unknown", "patients"] == 1


@pytest.mark.id("tst_og3y2a")
def test_each_patient_once():
    """A patient with two encounters counted once, at the first"""
    found = report(small([[20, 1, 7, "NO"], [10, 1, 7, "<30"]]))
    assert found.loc["All sources", "patients"] == 1
    assert found.loc["All sources", "readmitted"] == 1


@pytest.mark.id("tst_md06z1")
def test_opted_out_with_a_blank():
    """Every patient not opted out counted, with a blank row in opted_out"""
    found = report(small([[1, 1, 7, "NO"], [2, 2, 7, "NO"]], opted_out=[2, None]))
    assert found.loc["All sources", "patients"] == 1
