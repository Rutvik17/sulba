import csv

import pandas as pd
import pytest

from checks import key_problems


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


@pytest.mark.id("tst_3rwh6p")
def test_extract(table, mapping):
    """The extract's keys and codes hold"""
    assert key_problems(table, mapping) == []


@pytest.mark.id("tst_7e0txy")
def test_repeated_id(table, mapping):
    """Every row of an encounter id that repeats, counted"""
    rows = table.iloc[:5].copy()
    rows["encounter_id"] = [1, 2, 1, 3, 1]
    assert key_problems(rows, mapping) == [("encounter_id", "repeated", 3)]


@pytest.mark.id("tst_efrbva")
def test_codes_the_mapping_lacks(table, mapping):
    """Codes the mapping lacks, column by column in the mapping's order"""
    rows = table.iloc[:4].copy()
    rows["admission_source_id"] = [7, 27, 27, 1]
    rows["admission_type_id"] = [1, 2, 99, 3]
    assert key_problems(rows, mapping) == [
        ("admission_type_id", "not in the mapping", 1),
        ("admission_source_id", "not in the mapping", 2),
    ]


@pytest.mark.id("tst_whdovl")
def test_code_listed_twice(table, mapping):
    """A code the mapping lists twice"""
    types = mapping["admission_type_id"]
    doubled = {**mapping, "admission_type_id": pd.concat([types, types.iloc[[0]]])}
    assert key_problems(table, doubled) == [
        ("admission_type_id", "repeated in the mapping", 2)
    ]


@pytest.mark.id("tst_hk3cig")
def test_table_unchanged(table, mapping):
    """The table given left as it was"""
    before = table.copy()
    key_problems(table, mapping)
    pd.testing.assert_frame_equal(table, before)
