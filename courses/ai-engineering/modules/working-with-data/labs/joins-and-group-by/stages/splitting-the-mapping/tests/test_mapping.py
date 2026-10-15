import csv

import pandas as pd
import pytest

from report import read_mapping

PATH = "data/ids-mapping.csv"


@pytest.fixture(scope="module")
def written():
    """Each table's codes and descriptions as the file writes them, by the column each
    describes."""
    tables, current = {}, None
    with open(PATH, newline="") as file:
        for row in csv.reader(file):
            if not any(row):
                current = None
            elif current is None:
                current = tables.setdefault(row[0], {})
            else:
                current[int(row[0])] = row[1]
    return tables


@pytest.fixture(scope="module")
def mapping():
    return read_mapping(PATH)


@pytest.mark.id("tst_ehd51o")
def test_tables(mapping, written):
    """A table for each code column, of code and description"""
    assert list(mapping) == list(written)
    for table in mapping.values():
        assert list(table.columns) == ["code", "description"]


@pytest.mark.id("tst_cujpga")
def test_codes(mapping, written):
    """Every code once, as a whole number, in the file's order"""
    for column, table in mapping.items():
        assert pd.api.types.is_integer_dtype(table["code"]), column
        assert table["code"].tolist() == list(written[column]), column


@pytest.mark.id("tst_rd6ipa")
def test_descriptions(mapping, written):
    """Each description as written, without the spaces around it"""
    for column, table in mapping.items():
        expected = [text.strip() for text in written[column].values()]
        assert table["description"].tolist() == expected, column


@pytest.mark.id("tst_fyodc2")
def test_null_kept(mapping):
    """NULL kept as a description, not read as missing"""
    types = mapping["admission_type_id"].set_index("code")["description"]
    assert types[6] == "NULL"
    assert not any(table["description"].isna().any() for table in mapping.values())


@pytest.mark.id("tst_297h53")
def test_commas(mapping):
    """A description with a comma in it kept whole"""
    discharges = mapping["discharge_disposition_id"].set_index("code")["description"]
    assert discharges[19] == "Expired at home. Medicaid only, hospice."
