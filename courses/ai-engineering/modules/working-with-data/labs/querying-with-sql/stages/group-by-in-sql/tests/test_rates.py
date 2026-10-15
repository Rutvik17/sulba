import csv
import sqlite3

import pandas as pd
import pytest

from queries import load, rates


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
def connection(table):
    connection = sqlite3.connect(":memory:")
    load(connection, table, read_mapping("data/ids-mapping.csv"))
    return connection


@pytest.mark.id("tst_4g7dto")
def test_by_hand():
    """Encounters, readmissions and shares worked by hand, the highest share first"""
    connection = sqlite3.connect(":memory:")
    connection.execute("CREATE TABLE encounters (ward TEXT, readmitted TEXT)")
    wards = ["a", "b", "a", "c", "c", "c", None, None, None, None]
    outcomes = ["<30", "<30", ">30", "NO", "<30", "NO", "<30", "NO", "NO", ">30"]
    rows = list(zip(wards, outcomes, strict=True))
    connection.executemany("INSERT INTO encounters VALUES (?, ?)", rows)
    found = rates(connection, "ward", 1)
    assert list(found.columns) == ["value", "encounters", "readmitted", "share"]
    assert found["value"].iloc[:3].tolist() == ["b", "a", "c"]
    assert pd.isna(found["value"].iloc[3])
    assert found["encounters"].tolist() == [1, 2, 3, 4]
    assert found["readmitted"].tolist() == [1, 1, 1, 1]
    assert found["share"].tolist() == pytest.approx([1, 1 / 2, 1 / 3, 1 / 4])


@pytest.mark.id("tst_vtuwtc")
def test_null_group(connection, table):
    """A NULL counted as a group of its own"""
    found = rates(connection, "medical_specialty", 1)
    assert found["encounters"].sum() == len(table)
    missing = found[found["value"].isna()]
    assert missing["encounters"].tolist() == [table["medical_specialty"].isna().sum()]


@pytest.mark.id("tst_kw69wf")
def test_discharges(connection, table):
    """The rates of each discharge with at least 30 encounters, the highest share first"""
    found = rates(connection, "discharge_disposition_id", 30)
    soon = table["readmitted"] == "<30"
    groups = soon.groupby(table["discharge_disposition_id"])
    sizes = groups.size()
    assert sorted(found["value"]) == sorted(sizes[sizes >= 30].index)
    for row in found.itertuples():
        group = soon[table["discharge_disposition_id"] == row.value]
        assert row.encounters == len(group)
        assert row.readmitted == group.sum()
        assert row.share == pytest.approx(group.mean())
    assert found["share"].is_monotonic_decreasing


@pytest.mark.id("tst_4e8lge")
def test_column_refused(connection, table):
    """A name that isn't one of the table's columns refused, the table left as it was"""
    with pytest.raises(ValueError):
        rates(connection, "age; DROP TABLE encounters", 1)
    (count,) = connection.execute("SELECT COUNT(*) FROM encounters").fetchone()
    assert count == len(table)
