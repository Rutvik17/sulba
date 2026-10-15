from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from clean import clean

PATH = "data/encounters.csv"


@pytest.fixture(scope="module")
def text():
    """Every field of the extract as the file writes it, by encounter_id."""
    raw = pd.read_csv(PATH, dtype=str, keep_default_na=False)
    return raw.set_index(raw["encounter_id"].astype(int))


@pytest.fixture(scope="module")
def cleaned():
    return clean(PATH)


@pytest.mark.id("tst_7szgrf")
def test_tests_not_done(cleaned, text):
    """A1C and glucose tests not done kept as None"""
    for column in ["A1Cresult", "max_glu_serum"]:
        assert not cleaned[column].isna().any(), column
        expected = text.loc[cleaned["encounter_id"], column]
        assert cleaned[column].tolist() == expected.tolist(), column


@pytest.mark.id("tst_rt8717")
def test_earliest_in_any_order(tmp_path, text):
    """Each patient's earliest encounter, with the extract in another order"""
    header, *rows = Path(PATH).read_text().splitlines()
    order = np.random.default_rng(0).permutation(len(rows))
    shuffled = tmp_path / "shuffled.csv"
    shuffled.write_text("\n".join([header, *(rows[i] for i in order)]) + "\n")
    found = clean(shuffled)
    earliest = text.index.to_series().groupby(text["patient_nbr"].astype(int)).min()
    assert found["encounter_id"].tolist() == earliest.loc[found["patient_nbr"]].tolist()


@pytest.mark.id("tst_du5bd3")
def test_no_hospice(cleaned):
    """No encounter that ended in hospice care"""
    assert not cleaned["discharge_disposition_id"].isin([13, 14]).any()


@pytest.mark.id("tst_ivppss")
def test_readmitted_within_30_days(cleaned, text):
    """readmitted True only for a readmission within 30 days"""
    expected = text.loc[cleaned["encounter_id"], "readmitted"] == "<30"
    assert cleaned["readmitted"].tolist() == expected.tolist()
