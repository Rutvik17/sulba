import csv
import sqlite3

import pandas as pd
import pytest

from dashboard import report

UNKNOWN = {"NULL", "Not Available", "Not Mapped", "Unknown/Invalid"}


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


@pytest.fixture(scope="module")
def rows():
    table = pd.read_csv("data/encounters.csv", na_values=["?"], keep_default_na=False)
    opted_out = table["patient_nbr"].iloc[:3].tolist()
    return report(database(table, opted_out))


@pytest.mark.id("tst_7ufvf7")
def test_rows(rows):
    """A row for each admission source, then one for all of them"""
    assert rows.index.is_unique
    assert rows.index[-1] == "All sources"
    assert list(rows.columns) == ["patients", "readmitted", "share"]


@pytest.mark.id("tst_yh3oo7")
def test_unknown_together(rows):
    """The sources that stand for unknown counted together as Unknown"""
    assert "Unknown" in rows.index
    assert not set(rows.index) & UNKNOWN


@pytest.mark.id("tst_o8eg9g")
def test_shares(rows):
    """Each share between 0 and 1, and no more readmissions than patients"""
    assert rows["share"].between(0, 1).all()
    assert (rows["readmitted"] <= rows["patients"]).all()


@pytest.mark.id("tst_28qjtp")
def test_all_sources_adds_up(rows):
    """All sources counts every patient in the rows above it"""
    sources = rows.drop(index="All sources")
    assert rows.loc["All sources", "patients"] == sources["patients"].sum()
    assert rows.loc["All sources", "readmitted"] == sources["readmitted"].sum()
