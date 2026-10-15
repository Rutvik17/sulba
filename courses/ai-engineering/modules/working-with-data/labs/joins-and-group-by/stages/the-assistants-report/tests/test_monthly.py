import pytest

from monthly import report

UNKNOWN = {"NULL", "Not Available", "Not Mapped", "Unknown/Invalid"}


@pytest.fixture(scope="module")
def rows():
    return report("data/encounters.csv", "data/ids-mapping.csv")


@pytest.mark.id("tst_ogrmo1")
def test_rows(rows):
    """A row for each admission source, then one for all of them"""
    assert rows.index.is_unique
    assert rows.index[-1] == "All sources"
    assert list(rows.columns) == ["patients", "readmitted", "share"]


@pytest.mark.id("tst_w7obei")
def test_unknown_together(rows):
    """The sources that stand for unknown counted together as Unknown"""
    assert "Unknown" in rows.index
    assert not set(rows.index) & UNKNOWN


@pytest.mark.id("tst_lwwg3j")
def test_shares(rows):
    """Each share between 0 and 1, and no more readmissions than patients"""
    assert rows["share"].between(0, 1).all()
    assert (rows["readmitted"] <= rows["patients"]).all()


@pytest.mark.id("tst_0ejuto")
def test_all_sources_adds_up(rows):
    """All sources counts every patient in the rows above it"""
    sources = rows.drop(index="All sources")
    assert rows.loc["All sources", "patients"] == sources["patients"].sum()
    assert rows.loc["All sources", "readmitted"] == sources["readmitted"].sum()
