import pandas as pd
import pytest

from monthly import report

ENCOUNTERS, MAPPING = "data/encounters.csv", "data/ids-mapping.csv"


@pytest.fixture(scope="module")
def rows():
    return report(ENCOUNTERS, MAPPING)


def extract(tmp_path, encounters):
    """A small extract of the encounters given, each the extract's first row with the encounter,
    patient, admission source and outcome given, discharged home."""
    first = pd.read_csv(ENCOUNTERS, dtype=str, keep_default_na=False).iloc[0].to_dict()
    fields = ["encounter_id", "patient_nbr", "admission_source_id", "readmitted"]
    table = pd.DataFrame(
        [
            {
                **first,
                **dict(zip(fields, values, strict=True)),
                "discharge_disposition_id": "1",
            }
            for values in encounters
        ]
    )
    path = tmp_path / "extract.csv"
    table.to_csv(path, index=False)
    return path


@pytest.mark.id("tst_voqmx6")
def test_sources_named(rows):
    """Admission sources named from the mapping's table of admission sources"""
    assert {"Emergency Room", "Physician Referral"} <= set(rows.index)
    assert "Trauma Center" not in rows.index


@pytest.mark.id("tst_z1yvw1")
def test_code_the_mapping_lacks(tmp_path):
    """Every patient counted, one from a source the mapping lacks under Unknown"""
    path = extract(tmp_path, [["1", "1", "7", "NO"], ["2", "2", "27", "<30"]])
    found = report(path, MAPPING)
    assert found.loc["All sources", "patients"] == 2
    assert found.loc["Unknown", "patients"] == 1


@pytest.mark.id("tst_gj84ir")
def test_all_sources_share(rows):
    """The share for all sources is of every patient"""
    total = rows.loc["All sources"]
    assert total["share"] == pytest.approx(total["readmitted"] / total["patients"])


@pytest.mark.id("tst_svorvu")
def test_each_patient_once(tmp_path):
    """A patient with two encounters counted once, at the first"""
    path = extract(tmp_path, [["20", "1", "7", "NO"], ["10", "1", "7", "<30"]])
    found = report(path, MAPPING)
    assert found.loc["All sources", "patients"] == 1
    assert found.loc["All sources", "readmitted"] == 1
