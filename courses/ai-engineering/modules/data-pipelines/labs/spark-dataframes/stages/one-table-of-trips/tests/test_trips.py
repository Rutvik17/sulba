from functools import cache

import pyarrow.compute as pc
import pyarrow.parquet as pq
import pytest
from pyspark.sql import functions as F

from trips import trips

FILES = {
    "yellow": ("data/yellow_tripdata_2025-08.parquet", "tpep"),
    "green": ("data/green_tripdata_2025-08.parquet", "lpep"),
}
SCHEMA = (
    "struct<service:string,vendor:int,pickup_at:timestamp_ntz,dropoff_at:timestamp_ntz,"
    "passengers:int,distance:double,pickup_zone:int,dropoff_zone:int,payment:int,"
    "fare:double,tip:double,total:double>"
)


@cache
def expected(service):
    """A service's rows, totals and missing passenger counts, worked out in pyarrow."""
    path, prefix = FILES[service]
    table = pq.read_table(path)
    return {
        "trips": table.num_rows,
        "total": pc.sum(table["total_amount"]).as_py(),
        "tip": pc.sum(table["tip_amount"]).as_py(),
        "zones": pc.sum(table["PULocationID"]).as_py(),
        "passengers": pc.sum(table["passenger_count"]).as_py(),
        "unreported": table["passenger_count"].null_count,
        "first": pc.min(table[f"{prefix}_pickup_datetime"]).as_py(),
        "last": pc.max(table[f"{prefix}_dropoff_datetime"]).as_py(),
    }


def summary(spark):
    rows = (
        trips(spark)
        .groupBy("service")
        .agg(
            F.count("*").alias("trips"),
            F.sum("total").alias("total"),
            F.sum("tip").alias("tip"),
            F.sum("pickup_zone").alias("zones"),
            F.sum("passengers").alias("passengers"),
            F.count_if(F.col("passengers").isNull()).alias("unreported"),
            F.min("pickup_at").alias("first"),
            F.max("dropoff_at").alias("last"),
        )
        .collect()
    )
    return {row["service"]: row.asDict() for row in rows}


@pytest.mark.id("tst_on8w1z")
def test_columns(spark):
    """The table's columns and their types, in order"""
    assert trips(spark).schema.simpleString() == SCHEMA


@pytest.mark.id("tst_cp4bst")
def test_rows(spark):
    """Every trip of both services, once"""
    got = summary(spark)
    assert {service: row["trips"] for service, row in got.items()} == {
        service: expected(service)["trips"] for service in FILES
    }


@pytest.mark.id("tst_9ge2pf")
def test_values(spark):
    """Each service's values land in their own columns"""
    got = summary(spark)
    for service in FILES:
        want = expected(service)
        row = got[service]
        assert row["total"] == pytest.approx(want["total"], rel=1e-12)
        assert row["tip"] == pytest.approx(want["tip"], rel=1e-12)
        assert row["zones"] == want["zones"]
        assert row["passengers"] == want["passengers"]
        assert str(row["first"]) == str(want["first"])
        assert str(row["last"]) == str(want["last"])


@pytest.mark.id("tst_oowj3z")
def test_unreported(spark):
    """A trip that reports no passengers keeps a null, not 0"""
    got = summary(spark)
    for service in FILES:
        assert got[service]["unreported"] == expected(service)["unreported"] > 0
