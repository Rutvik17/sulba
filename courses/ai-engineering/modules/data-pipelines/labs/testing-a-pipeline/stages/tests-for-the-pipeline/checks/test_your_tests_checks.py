import sys

import pytest

pytest_plugins = ["pytester"]

# The modules a run of your tests imports, forgotten after it so the next run starts afresh.
MODULES = ["weather", "daily", "rain", "test_pipeline", "conftest"]

# A conftest that gives your tests the Spark session these checks run in, and plants one
# problem in your pipeline: it wraps weather, daily or against_dry_days, so every test of yours
# that calls it meets the problem, and leaves the rest of the pipeline as it is.
PLANTED = """
import pytest
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

import daily
import rain
import weather

PROBLEM = None
UNITS = {"rain_mm": "PRCP", "high_c": "TMAX", "low_c": "TMIN", "wind_ms": "AWND"}


@pytest.fixture(scope="session")
def spark_session():
    return SparkSession.getActiveSession()


def planted_weather(original):
    def weather_(spark):
        result = original(spark)
        columns = result.columns
        if PROBLEM == "tenths":
            return result.select(
                *[(F.col(name) * 10).alias(name) if name in UNITS else name for name in columns]
            )
        raw = spark.read.option("header", True).csv(weather.WEATHER).select(
            F.to_date("DATE").alias("day"),
            *[
                (F.trim(F.col(column)).cast("int") / 10).alias(f"raw_{name}")
                for name, column in UNITS.items()
            ],
        )
        return result.join(raw, "day", "left").select(
            *[F.coalesce(name, f"raw_{name}").alias(name) if name in UNITS else name for name in columns]
        )

    return weather_


def planted_daily(original):
    def daily_(spark, flagged, weather_):
        result = original(spark, flagged, weather_)
        columns = result.columns
        if PROBLEM == "no trips":
            return result.where(F.col("trips") > 0)
        if PROBLEM == "weekday":
            changed = F.date_format(F.date_add("day", 1), "EEEE")
            return result.withColumn("weekday", changed).select(*columns)
        return result.withColumn("wet", F.col("rain_mm") > 1.0).select(*columns)

    return daily_


def planted_against(original):
    def against_dry_days(daily_):
        columns = original(daily_).columns
        result = original(daily_.withColumn("weekday", F.lit("")))
        weekdays = daily_.select("borough", "day", "weekday")
        return result.drop("weekday").join(weekdays, ["borough", "day"]).select(*columns)

    return against_dry_days


if PROBLEM in ("tenths", "quality"):
    weather.weather = planted_weather(weather.weather)
elif PROBLEM in ("no trips", "weekday", "wet"):
    daily.daily = planted_daily(daily.daily)
else:
    rain.against_dry_days = planted_against(rain.against_dry_days)
"""

# Each run stops at the first of your tests that fails, which is enough to catch the problem.
OPTIONS = [
    "-p",
    "no:terminal",
    "-x",
    "-p",
    "no:cacheprovider",
    "-p",
    "no:unraisableexception",
    "-p",
    "sulba_fixtures",
]


@pytest.fixture
def caught(pytester, pytestconfig, monkeypatch, spark):
    """Whether one of your tests fails on your pipeline with the problem planted."""
    root = pytestconfig.rootpath

    def run(problem):
        (pytester.path / "test_pipeline.py").write_text(
            (root / "test_pipeline.py").read_text()
        )
        planted = PLANTED.replace("PROBLEM = None", f"PROBLEM = {problem!r}")
        (pytester.path / "conftest.py").write_text(planted)
        monkeypatch.chdir(root)
        try:
            recorder = pytester.inline_run(
                *OPTIONS, str(pytester.path / "test_pipeline.py")
            )
        finally:
            for name in MODULES:
                sys.modules.pop(name, None)
        return recorder.countoutcomes()[2] > 0

    return run


@pytest.mark.id("tst_pl8e3g")
def test_catch_tenths(caught):
    """They catch weather left in tenths"""
    assert caught("tenths"), "Every one of your tests passed on it"


@pytest.mark.id("tst_jn42c9")
def test_catch_failed_values(caught):
    """They catch a value kept after it failed a quality check"""
    assert caught("quality"), "Every one of your tests passed on it"


@pytest.mark.id("tst_0p5yk7")
def test_catch_missing_days(caught):
    """They catch a borough's day dropped for having no trips"""
    assert caught("no trips"), "Every one of your tests passed on it"


@pytest.mark.id("tst_podlpb")
def test_catch_weekdays(caught):
    """They catch each day given the next day's weekday"""
    assert caught("weekday"), "Every one of your tests passed on it"


@pytest.mark.id("tst_enrwvc")
def test_catch_wet_days(caught):
    """They catch a day of exactly 1 mm left out of the wet days"""
    assert caught("wet"), "Every one of your tests passed on it"


@pytest.mark.id("tst_tz1554")
def test_catch_every_dry_day(caught):
    """They catch wet days compared with every dry day, not those of their weekday"""
    assert caught("every dry day"), "Every one of your tests passed on it"
