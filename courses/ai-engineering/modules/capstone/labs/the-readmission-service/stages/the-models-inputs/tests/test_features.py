import pandas as pd
import pytest

from features import features, stays

INPUTS = [
    "time_in_hospital",
    "num_lab_procedures",
    "num_procedures",
    "num_medications",
    "number_outpatient",
    "number_emergency",
    "number_inpatient",
    "number_diagnoses",
    "age",
    "gender",
    "admission_type_id",
    "admission_source_id",
    "discharge_disposition_id",
    "A1Cresult",
    "insulin",
    "change",
    "diabetesMed",
]
CODES = ["admission_type_id", "admission_source_id", "discharge_disposition_id"]
# A request's fields: the stay's age band, its counts and its categories, as in the extract.
FIELDS = ["age", *[name for name in INPUTS if name != "age"]]


@pytest.fixture(scope="module")
def table():
    return stays("data/encounters.csv")


def request(row):
    """The stay in row, as a request's JSON body would bring it: numbers and text."""
    return {
        name: row[name].item() if hasattr(row[name], "item") else row[name]
        for name in FIELDS
    }


@pytest.mark.id("tst_2qfuzg")
def test_inputs(table):
    """Gives the model's inputs, in order"""
    assert list(features(table).columns) == INPUTS


@pytest.mark.id("tst_3xobdc")
def test_age(table):
    """Puts each age at the middle of its band"""
    bands = (
        table.drop_duplicates("age")
        .set_index("age")
        .loc[["[0-10)", "[70-80)", "[90-100)"]]
    )
    assert features(bands.reset_index())["age"].tolist() == [5, 75, 95]


@pytest.mark.id("tst_gpyblm")
def test_counts(table):
    """Keeps the counts as they are"""
    inputs = features(table)
    for name in INPUTS[:8]:
        assert inputs[name].tolist() == table[name].tolist(), name


@pytest.mark.id("tst_seocjx")
def test_categories_as_text(table):
    """Writes the codes and the categories as text"""
    inputs = features(table)
    for name in INPUTS[9:]:
        assert all(isinstance(value, str) for value in inputs[name]), name
    assert (
        inputs["admission_source_id"].tolist()
        == table["admission_source_id"].astype(str).tolist()
    )


@pytest.mark.id("tst_48so8r")
def test_request_like_table(table):
    """Gives a request's stay the inputs it has in the extract"""
    for index in table.index[:20]:
        sent = features(pd.DataFrame([request(table.loc[index])]))
        kept = features(table.loc[[index]])
        assert sent.to_dict("records") == kept.to_dict("records")


@pytest.mark.id("tst_wcfksv")
def test_codes_sent_as_text(table):
    """Gives codes sent as text the inputs they have as numbers"""
    stay = request(table.iloc[0])
    as_text = {**stay, **{name: str(stay[name]) for name in CODES}}
    assert features(pd.DataFrame([as_text])).to_dict("records") == features(
        pd.DataFrame([stay])
    ).to_dict("records")


@pytest.mark.id("tst_bvk47h")
def test_rows_untouched(table):
    """Leaves the rows it's given as they were"""
    rows = table.head(50).copy()
    features(rows)
    assert rows.equals(table.head(50))


@pytest.mark.id("tst_wfb1n3")
def test_keeps_index(table):
    """Keeps each row's index"""
    assert features(table).index.equals(table.index)
