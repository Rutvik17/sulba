import csv
from datetime import date

import pytest

import weather as module
from weather import weather

COLUMNS = [
    ("day", "date"),
    ("rain_mm", "double"),
    ("trace", "boolean"),
    ("high_c", "double"),
    ("low_c", "double"),
    ("wind_ms", "double"),
    ("fog", "boolean"),
    ("thunder", "boolean"),
    ("haze", "boolean"),
]
HEADER = (
    "STATION,DATE,AWND,AWND_ATTRIBUTES,PRCP,PRCP_ATTRIBUTES,SNOW,SNOW_ATTRIBUTES,TMAX,"
    "TMAX_ATTRIBUTES,TMIN,TMIN_ATTRIBUTES,WT01,WT01_ATTRIBUTES,WT03,WT03_ATTRIBUTES,WT08,"
    "WT08_ATTRIBUTES"
)


def expected():
    """Each day's values, read from the file with the csv module."""
    rows = {}
    with open("data/central-park-2025-08.csv", encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):

            def tenths(column):
                return int(row[column]) / 10

            rows[date.fromisoformat(row["DATE"])] = (
                tenths("PRCP"),
                row["PRCP_ATTRIBUTES"].split(",")[0] == "T",
                tenths("TMAX"),
                tenths("TMIN"),
                tenths("AWND"),
                *(row[column].strip() == "1" for column in ("WT01", "WT03", "WT08")),
            )
    return rows


@pytest.mark.id("tst_1qce2s")
def test_columns(spark):
    """The table's columns and their types"""
    assert weather(spark).dtypes == COLUMNS


@pytest.mark.id("tst_gbxd7s")
def test_every_day(spark):
    """Each day's rain, trace, temperatures, wind and weather types, in units"""
    rows = {row["day"]: tuple(row)[1:] for row in weather(spark).collect()}
    assert rows == pytest.approx(expected())


@pytest.mark.id("tst_1f5muv")
def test_failed_quality_check(spark, tmp_path, monkeypatch):
    """A value with a quality flag is missing, and the day's other values stay"""
    path = tmp_path / "weather.csv"
    path.write_text(
        HEADER
        + "\n"
        + '"USW00094728","2025-08-13","   31",",,W","  180",",,W,2400","    0",",,W,2400",'
        + '"  999",",X,W","  233",",,W",,,"    1",",,W",,\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(module, "WEATHER", str(path))
    (row,) = weather(spark).collect()
    assert row["high_c"] is None
    assert (row["rain_mm"], row["low_c"], row["wind_ms"]) == pytest.approx(
        (18.0, 23.3, 3.1)
    )
    assert (row["fog"], row["thunder"], row["haze"]) == (False, True, False)
