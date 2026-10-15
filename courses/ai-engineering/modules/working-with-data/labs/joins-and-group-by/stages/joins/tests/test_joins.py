import pandas as pd
import pytest

from report import describe, read_mapping, unmatched


@pytest.fixture(scope="module")
def mapping():
    return read_mapping("data/ids-mapping.csv")


@pytest.fixture(scope="module")
def table():
    return pd.read_csv("data/encounters.csv", na_values=["?"], keep_default_na=False)


@pytest.fixture(scope="module")
def described(table, mapping):
    return describe(table, mapping)


def encounters(**codes):
    """A small table of encounters with the codes given, the others 1."""
    columns = ["admission_type_id", "discharge_disposition_id", "admission_source_id"]
    count = len(next(iter(codes.values())))
    table = {"encounter_id": list(range(1, count + 1))}
    for column in columns:
        table[column] = codes.get(column, [1] * count)
    return pd.DataFrame(table)


@pytest.mark.id("tst_qwjzge")
def test_every_encounter(described, table):
    """Every encounter once, in the table's order"""
    assert described["encounter_id"].tolist() == table["encounter_id"].tolist()


@pytest.mark.id("tst_01rbto")
def test_descriptions(described, mapping):
    """Each code's description beside it"""
    for column, codes in mapping.items():
        words = dict(zip(codes["code"], codes["description"], strict=True))
        expected = [words[code] for code in described[column]]
        assert described[column.removesuffix("_id")].tolist() == expected, column


@pytest.mark.id("tst_lcv56c")
def test_code_the_mapping_lacks(mapping):
    """A code the mapping lacks kept, with its description missing"""
    found = describe(encounters(admission_type_id=[1, 99]), mapping)
    assert found["encounter_id"].tolist() == [1, 2]
    assert found["admission_type"].iloc[0] == "Emergency"
    assert pd.isna(found["admission_type"].iloc[1])


@pytest.mark.id("tst_s51mos")
def test_code_twice(mapping):
    """A mapping with a code twice raises an error, rather than doubling encounters"""
    types = mapping["admission_type_id"]
    doubled = {**mapping, "admission_type_id": pd.concat([types, types.iloc[[0]]])}
    with pytest.raises(pd.errors.MergeError):
        describe(encounters(admission_type_id=[1, 2]), doubled)


@pytest.mark.id("tst_kud82r")
def test_unmatched(mapping, table):
    """The codes the mapping lacks, by column, smallest first"""
    assert unmatched(table, mapping) == {column: [] for column in mapping}
    new = encounters(
        admission_type_id=[1, 99, 98, 99], admission_source_id=[7, 27, 7, 7]
    )
    assert unmatched(new, mapping) == {
        "admission_type_id": [98, 99],
        "discharge_disposition_id": [],
        "admission_source_id": [27],
    }


@pytest.mark.id("tst_7ygv7b")
def test_table_unchanged(table, mapping):
    """The table given left as it was"""
    before = table.copy()
    describe(table, mapping)
    unmatched(table, mapping)
    pd.testing.assert_frame_equal(table, before)
