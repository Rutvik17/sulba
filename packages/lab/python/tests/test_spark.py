import json

from sulba_runner import run

SESSION = {
    "tests/test_orders.py": """
import pytest
from pyspark.sql import functions as F
from pyspark.testing import assertDataFrameEqual


@pytest.mark.id("tst_spk001")
def test_totals(spark):
    orders = spark.createDataFrame(
        [("UK", 120.5), ("US", 15.25), ("UK", 80.0)], "country STRING, amount DOUBLE"
    )
    totals = orders.groupBy("country").agg(F.sum("amount").alias("total"))
    expected = spark.createDataFrame(
        [("UK", 200.5), ("US", 15.25)], "country STRING, total DOUBLE"
    )
    assertDataFrameEqual(totals, expected)


@pytest.mark.id("tst_spk002")
def test_a_view(spark):
    spark.range(3).createOrReplaceTempView("numbers")
    assert spark.sql("SELECT sum(id) FROM numbers").first()[0] == 3


@pytest.mark.id("tst_spk003")
def test_no_view_left_and_utc(spark):
    assert spark.catalog.listTables() == []
    assert spark.conf.get("spark.sql.session.timeZone") == "UTC"
""",
}


def test_a_runs_tests_share_a_spark_session_on_sail_and_start_with_no_views() -> None:
    result = json.loads(run(json.dumps(SESSION), json.dumps(["tests/test_orders.py"])))
    assert [(test["name"], test["status"], test["message"]) for test in result["tests"]] == [
        ("test_totals", "pass", None),
        ("test_a_view", "pass", None),
        ("test_no_view_left_and_utc", "pass", None),
    ]
