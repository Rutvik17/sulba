import pytest

from report import daily_report

COLUMNS = [
    ("service", "string"),
    ("day", "int"),
    ("trips", "bigint"),
    ("card_trips", "bigint"),
    ("fares", "double"),
    ("tips", "double"),
    ("takings", "double"),
    ("charges", "double"),
]


@pytest.mark.id("tst_uqj0t9")
def test_columns(spark):
    """The report's columns and their types"""
    assert daily_report(spark).dtypes == COLUMNS


@pytest.mark.id("tst_rf10it")
def test_each_day(spark):
    """A row for each service on each day of August"""
    rows = daily_report(spark).collect()
    assert sorted((row["service"], row["day"]) for row in rows) == sorted(
        (service, day) for service in ("green", "yellow") for day in range(1, 32)
    )


@pytest.mark.id("tst_xxp48t")
def test_amounts(spark):
    """Card trips are some of the trips, and the takings and charges are positive"""
    for row in daily_report(spark).collect():
        assert 0 <= row["card_trips"] <= row["trips"]
        assert row["takings"] > 0
        assert row["charges"] >= 0
