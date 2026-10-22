"""Probe classic PySpark's file reads and writes, and how collected timestamps follow the local
time zone, with each error's Java causes in full.

Usage: python probe.py <out.json> <workdir>
"""

import datetime
import json
import sys
import time
from pathlib import Path

OUT, WORK = Path(sys.argv[1]), Path(sys.argv[2])
WORK.mkdir(parents=True, exist_ok=True)

from pyspark.sql import SparkSession  # noqa: E402
from pyspark.sql import functions as F  # noqa: E402

spark = (
    SparkSession.builder.master("local[2]")
    .config("spark.ui.enabled", "false")
    .config("spark.sql.session.timeZone", "UTC")
    .getOrCreate()
)
orders = spark.createDataFrame(
    [(1, "UK", 120.5), (2, "US", 15.25), (3, None, 99.99)], "id INT, country STRING, amount DOUBLE"
)
(WORK / "in.csv").write_text("id,country\n1,UK\n2,US\n", encoding="utf-8")
HERE = Path(__file__).parent


def rows(df):
    return sorted(repr(tuple(r)) for r in df.collect())


def causes(error):
    """The error's type, and every line of its message that names an exception or a cause."""
    lines = str(error).splitlines()
    kept = [line.strip() for line in lines if "Exception" in line or "Caused by" in line or "Error" in line]
    return {"type": type(error).__name__, "first": lines[0][:300] if lines else "", "causes": kept[:25]}


CASES = {
    "parquet_read": lambda: rows(spark.read.parquet(str(HERE / "orders.parquet"))),
    "csv_read": lambda: rows(spark.read.option("header", True).csv(str(WORK / "in.csv"))),
    "parquet_write": lambda: orders.write.mode("overwrite").parquet(str(WORK / "out.parquet")),
    "csv_write": lambda: orders.write.mode("overwrite").option("header", True).csv(str(WORK / "out.csv")),
    "json_write": lambda: orders.write.mode("overwrite").json(str(WORK / "out.json")),
    "temp_view_sql": lambda: (orders.createOrReplaceTempView("orders"), rows(spark.sql("SELECT country, SUM(amount) FROM orders GROUP BY country")))[1],
    "timestamp_collect": lambda: rows(spark.sql("SELECT TIMESTAMP '2026-03-29 01:30:00' AS t")),
    "timestamp_as_string": lambda: rows(spark.sql("SELECT CAST(TIMESTAMP '2026-03-29 01:30:00' AS STRING) AS t")),
    "timestamp_ntz_collect": lambda: rows(spark.sql("SELECT TIMESTAMP_NTZ '2026-03-29 01:30:00' AS t")),
    "to_pandas_timestamp": lambda: str(spark.sql("SELECT TIMESTAMP '2026-03-29 01:30:00' AS t").toPandas()["t"][0]),
}

results = {
    "local_zone": str(datetime.datetime.now().astimezone().tzinfo),
    "time_tzname": list(time.tzname),
    "cases": {},
}
for name, case in CASES.items():
    try:
        value = {"value": case()}
    except Exception as e:  # record the failure as the result
        value = {"error": causes(e)}
    results["cases"][name] = value
spark.stop()
OUT.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
