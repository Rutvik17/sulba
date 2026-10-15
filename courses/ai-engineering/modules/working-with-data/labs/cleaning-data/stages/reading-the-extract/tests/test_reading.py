import pandas as pd
import pytest

from cleaning import missing_shares, read_encounters

PATH = "data/encounters.csv"


@pytest.fixture(scope="module")
def text():
    """Every field of the extract as the file writes it."""
    return pd.read_csv(PATH, dtype=str, keep_default_na=False)


@pytest.fixture(scope="module")
def table():
    return read_encounters(PATH)


@pytest.mark.id("tst_qgoah5")
def test_every_encounter(table, text):
    """Every encounter, with every column"""
    assert table.shape == text.shape
    assert list(table.columns) == list(text.columns)


@pytest.mark.id("tst_2xqw4k")
def test_question_marks(table, text):
    """Each question mark read as missing, and no other value"""
    for column in text.columns:
        assert table[column].isna().tolist() == (text[column] == "?").tolist(), column


@pytest.mark.id("tst_61m11u")
def test_tests_not_done(table, text):
    """An A1C or glucose test not done kept as None"""
    for column in ["A1Cresult", "max_glu_serum"]:
        assert (table[column] == "None").sum() == (text[column] == "None").sum() > 0


@pytest.mark.id("tst_6qatur")
def test_whole_numbers(table):
    """Ids and counts read as whole numbers"""
    for column in [
        "encounter_id",
        "patient_nbr",
        "time_in_hospital",
        "num_medications",
    ]:
        assert pd.api.types.is_integer_dtype(table[column]), column


@pytest.mark.id("tst_8ol4ip")
def test_shares_by_hand():
    """Shares worked by hand, only for columns with a gap, the largest first"""
    table = pd.DataFrame(
        {"a": ["x", None, "y", "z"], "b": [1, 2, 3, 4], "c": [1.0, None, None, 4.0]}
    )
    shares = missing_shares(table)
    assert list(shares.index) == ["c", "a"]
    assert list(shares) == [0.5, 0.25]


@pytest.mark.id("tst_p739ha")
def test_shares_of_the_extract(table, text):
    """The extract's shares, weight first"""
    expected = (text == "?").mean()
    expected = expected[expected > 0].sort_values(ascending=False)
    shares = missing_shares(table)
    assert list(shares.index) == list(expected.index)
    assert shares.to_numpy() == pytest.approx(expected.to_numpy())
