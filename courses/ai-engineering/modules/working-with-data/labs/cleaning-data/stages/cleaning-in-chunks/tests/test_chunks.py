import pandas as pd
import pytest

from cleaning import clean_chunks

PATH = "data/encounters.csv"
UNKNOWN_CODES = {
    "admission_type_id": [5, 6, 8],
    "discharge_disposition_id": [18, 25, 26],
    "admission_source_id": [9, 15, 17, 20, 21],
}
DEATH_OR_HOSPICE = [11, 13, 14, 19, 20, 21]


@pytest.fixture(scope="module")
def whole():
    """The whole extract, read at once."""
    return pd.read_csv(PATH, na_values=["?"], keep_default_na=False)


@pytest.fixture(scope="module")
def expected(whole):
    """The whole extract, cleaned at once."""
    table = whole.copy()
    for column, codes in UNKNOWN_CODES.items():
        table[column] = table[column].astype("Int64").mask(table[column].isin(codes))
    table["gender"] = table["gender"].mask(table["gender"] == "Unknown/Invalid")
    first = table.sort_values("encounter_id").drop_duplicates("patient_nbr")
    return first[~first["discharge_disposition_id"].isin(DEATH_OR_HOSPICE)]


def chunks(whole, size):
    """The extract in chunks of size rows, each column read as the whole extract reads it."""
    types = whole.dtypes.to_dict()
    return pd.read_csv(
        PATH, na_values=["?"], keep_default_na=False, dtype=types, chunksize=size
    )


@pytest.fixture(scope="module")
def found(whole):
    return clean_chunks(chunks(whole, 1000))


def same(found, expected):
    pd.testing.assert_frame_equal(
        found.sort_values("encounter_id").reset_index(drop=True),
        expected.reset_index(drop=True),
    )


@pytest.mark.id("tst_jtnlsj")
def test_chunks_of_1000(found, expected):
    """The whole extract's table, from chunks of 1,000 rows"""
    same(found, expected)


@pytest.mark.id("tst_m3rkk8")
def test_one_chunk(whole, expected):
    """The same table from the whole extract in one chunk"""
    found = clean_chunks(chunks(whole, len(whole)))
    assert sorted(found["encounter_id"]) == expected["encounter_id"].tolist()


@pytest.mark.id("tst_eis34l")
def test_in_order(found):
    """In order of encounter_id"""
    assert found["encounter_id"].is_monotonic_increasing
