import pandas as pd
import pytest

from cleaning import drop_sparse, mark_unknown, read_encounters

UNKNOWN = {
    "admission_type_id": {5, 6, 8},
    "discharge_disposition_id": {18, 25, 26},
    "admission_source_id": {9, 15, 17, 20, 21},
}


@pytest.fixture(scope="module")
def table():
    return read_encounters("data/encounters.csv")


@pytest.fixture(scope="module")
def marked(table):
    return mark_unknown(table)


@pytest.mark.id("tst_8k1lhz")
def test_codes(table, marked):
    """Each code for unknown read as missing, and every other code kept"""
    for column, codes in UNKNOWN.items():
        unknown = table[column].isin(codes)
        assert marked[column].isna().tolist() == unknown.tolist(), column
        assert marked[column][~unknown].tolist() == table[column][~unknown].tolist(), (
            column
        )


@pytest.mark.id("tst_8libvt")
def test_whole_numbers(marked):
    """Code columns still whole numbers"""
    for column in UNKNOWN:
        assert pd.api.types.is_integer_dtype(marked[column]), column


@pytest.mark.id("tst_z5wu8n")
def test_gender():
    """A gender of Unknown/Invalid read as missing"""
    table = pd.DataFrame(
        {
            "gender": ["Female", "Unknown/Invalid", "Male"],
            "admission_type_id": [1, 6, 3],
            "discharge_disposition_id": [1, 1, 25],
            "admission_source_id": [7, 17, 1],
        }
    )
    marked = mark_unknown(table)
    assert marked["gender"].isna().tolist() == [False, True, False]
    assert marked["discharge_disposition_id"].isna().tolist() == [False, False, True]


@pytest.mark.id("tst_kvcabk")
def test_table_unchanged(table):
    """The table given left as it was"""
    before = table.copy()
    mark_unknown(table)
    drop_sparse(table, 0.5)
    pd.testing.assert_frame_equal(table, before)


@pytest.mark.id("tst_g60qre")
def test_drop_sparse(marked):
    """Columns over the limit dropped, and every row and other column kept in order"""
    half = drop_sparse(marked, 0.5)
    assert [c for c in marked.columns if c not in half] == ["weight"]
    kept = drop_sparse(marked, 0.3)
    gone = {"weight", "medical_specialty", "payer_code"}
    assert list(kept.columns) == [c for c in marked.columns if c not in gone]
    assert len(kept) == len(marked)


@pytest.mark.id("tst_hbdqlm")
def test_drop_sparse_by_hand():
    """A column missing exactly at the limit kept"""
    table = pd.DataFrame({"a": [1.0, None], "b": [None, None], "c": [1, 2]})
    assert list(drop_sparse(table, 0.5).columns) == ["a", "c"]
