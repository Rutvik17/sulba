"""Tests for the pipeline: the weather, the daily table and the wet days against dry ones."""

from weather import weather


def test_weather_columns(spark):
    assert [name for name, _ in weather(spark).dtypes] == [
        "day",
        "rain_mm",
        "trace",
        "high_c",
        "low_c",
        "wind_ms",
        "fog",
        "thunder",
        "haze",
    ]
