import pandas as pd
import pytest

from clean import clean


@pytest.fixture(scope="module")
def cleaned():
    return clean("data/encounters.csv")


@pytest.mark.id("tst_o14vnv")
def test_one_row_per_patient(cleaned):
    """One row per patient, in order of encounter_id"""
    assert cleaned["patient_nbr"].is_unique
    assert cleaned["encounter_id"].is_monotonic_increasing


@pytest.mark.id("tst_ogx945")
def test_no_question_marks(cleaned):
    """No question mark left in any column"""
    assert not (cleaned.astype(str) == "?").any().any()


@pytest.mark.id("tst_4p5gbm")
def test_unknown_codes(cleaned):
    """Codes for unknown read as missing"""
    assert not cleaned["admission_type_id"].isin([5, 6, 8]).any()
    assert not cleaned["admission_source_id"].isin([9, 15, 17, 20, 21]).any()
    assert cleaned["admission_type_id"].isna().any()


@pytest.mark.id("tst_p4krub")
def test_no_deaths(cleaned):
    """No encounter that ended in the patient's death"""
    assert not cleaned["discharge_disposition_id"].isin([11, 19, 20, 21]).any()


@pytest.mark.id("tst_sm2gmx")
def test_readmitted_is_boolean(cleaned):
    """readmitted is True or False"""
    assert pd.api.types.is_bool_dtype(cleaned["readmitted"])
    assert cleaned["readmitted"].any() and not cleaned["readmitted"].all()
