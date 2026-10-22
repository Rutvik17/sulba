"""Run the same PySpark cases on one engine and write each case's result as JSON.

Usage: python compare.py <sail|classic|connect-local> <out.json> <workdir>
"""

import json
import os
import sys
import time
from pathlib import Path

ENGINE, OUT, WORK = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])
WORK.mkdir(parents=True, exist_ok=True)

t0 = time.perf_counter()
from pyspark.sql import SparkSession, Window  # noqa: E402
from pyspark.sql import functions as F  # noqa: E402

server = None
if ENGINE == "sail":
    from pysail.spark import SparkConnectServer

    server = SparkConnectServer()
    server.start()
    _, port = server.listening_address
    builder = SparkSession.builder.remote(f"sc://localhost:{port}")
elif ENGINE == "classic":
    builder = SparkSession.builder.master("local[2]").config("spark.ui.enabled", "false")
elif ENGINE == "connect-local":
    builder = SparkSession.builder.remote("local[2]").config("spark.ui.enabled", "false")
else:
    raise SystemExit(f"unknown engine {ENGINE}")
spark = builder.getOrCreate()
startup = time.perf_counter() - t0
spark.conf.set("spark.sql.session.timeZone", "UTC")

MESSY = WORK / "customers.csv"
MESSY.write_text(
    "id,name,email,signed_up,spend\n"
    "1,  Ada Lovelace ,ADA@Example.com,05/01/2026,120.50\n"
    "2,Grace Hopper,grace@example.com,2026-01-20,N/A\n"
    '3,"Torvalds, Linus",linus@example.com,31/02/2026,15\n'
    "4,,missing@example.com,,\n"
    "5,Extra Column,x@example.com,01/03/2026,9.99,surplus\n"
    "6,Short Row\n"
    "1,Ada Lovelace,ada@example.com,05/01/2026,120.50\n",
    encoding="utf-8",
)


def rows(df, sort=True):
    data = [tuple(r) for r in df.collect()]
    if sort:
        data = sorted(data, key=repr)
    return {"schema": df.schema.simpleString(), "rows": [repr(r) for r in data]}


customers = spark.createDataFrame(
    [(1, "  Ada ", "UK"), (2, "grace", "us"), (3, "Linus", "FI"), (4, "Ada", "UK")],
    "customer_id INT, name STRING, country STRING",
)
orders = spark.createDataFrame(
    [
        (10, 1, "2026-01-05", 120.50),
        (11, 1, "2026-02-11", 80.00),
        (12, 2, "2026-01-20", 15.25),
        (13, 3, "2026-03-02", None),
        (14, 9, "2026-03-03", 99.99),
    ],
    "order_id INT, customer_id INT, ordered STRING, amount DOUBLE",
)
customers.createOrReplaceTempView("customers")
orders.createOrReplaceTempView("orders")

CASES = {
    "join_groupby_agg": lambda: rows(
        orders.join(customers.withColumn("country", F.upper("country")), "customer_id", "left")
        .groupBy("country")
        .agg(F.count("order_id").alias("n"), F.sum("amount").alias("total"), F.avg("amount").alias("mean"))
    ),
    "sql_cte_window_rank": lambda: rows(
        spark.sql(
            "WITH s AS (SELECT c.customer_id, trim(c.name) AS name, sum(o.amount) AS total "
            "FROM customers c JOIN orders o ON o.customer_id = c.customer_id "
            "GROUP BY c.customer_id, trim(c.name)) "
            "SELECT name, total, rank() OVER (ORDER BY total DESC) AS place FROM s"
        )
    ),
    "orderby_default_nulls": lambda: rows(orders.select("amount").orderBy("amount"), sort=False),
    "orderby_desc_nulls": lambda: rows(orders.select("amount").orderBy(F.col("amount").desc()), sort=False),
    "csv_explicit_schema_permissive": lambda: rows(
        spark.read.option("header", True)
        .option("nullValue", "N/A")
        .schema("id INT, name STRING, email STRING, signed_up STRING, spend DOUBLE")
        .csv(str(MESSY))
    ),
    "csv_infer_schema": lambda: rows(
        spark.read.option("header", True).option("inferSchema", True).csv(str(MESSY))
    ),
    "csv_dropmalformed": lambda: rows(
        spark.read.option("header", True)
        .option("mode", "DROPMALFORMED")
        .schema("id INT, name STRING, email STRING, signed_up STRING, spend DOUBLE")
        .csv(str(MESSY))
    ),
    "clean_strings_dates": lambda: rows(
        spark.read.option("header", True)
        .option("nullValue", "N/A")
        .schema("id INT, name STRING, email STRING, signed_up STRING, spend DOUBLE")
        .csv(str(MESSY))
        .select(
            "id",
            F.initcap(F.trim("name")).alias("name"),
            F.lower(F.trim("email")).alias("email"),
            F.coalesce(
                F.try_to_timestamp("signed_up", F.lit("dd/MM/yyyy")).cast("date"),
                F.try_to_timestamp("signed_up", F.lit("yyyy-MM-dd")).cast("date"),
            ).alias("signed_up"),
            F.regexp_replace("email", "@.*$", "").alias("user"),
        )
        .dropDuplicates(["id"])
    ),
    "to_date_bad_value": lambda: rows(spark.sql("SELECT to_date('31/02/2026', 'dd/MM/yyyy') AS d")),
    "cast_bad_int": lambda: rows(spark.sql("SELECT CAST('12a' AS INT) AS v")),
    "try_cast_bad_int": lambda: rows(spark.sql("SELECT try_cast('12a' AS INT) AS v")),
    "divide_by_zero": lambda: rows(spark.sql("SELECT 1 / 0 AS v")),
    "int_overflow": lambda: rows(spark.sql("SELECT 2147483647 + CAST(1 AS INT) AS v")),
    "round_half": lambda: rows(
        spark.sql("SELECT round(2.5) a, round(-2.5) b, bround(2.5) c, round(2.675, 2) d, round(CAST(2.675 AS DOUBLE), 2) e")
    ),
    "decimal_arith": lambda: rows(
        spark.sql("SELECT CAST(1.10 AS DECIMAL(10,2)) * 3 AS a, sum(x) AS s, avg(x) AS m FROM VALUES (CAST(0.1 AS DECIMAL(10,1))), (CAST(0.2 AS DECIMAL(10,1))) AS t(x)")
    ),
    "double_sum_avg": lambda: rows(
        spark.range(0, 1000).select((F.col("id") * F.lit(0.1)).alias("x")).agg(F.sum("x").alias("s"), F.avg("x").alias("m"), F.stddev("x").alias("sd"))
    ),
    "agg_result_types": lambda: rows(
        orders.agg(F.count("*").alias("c"), F.sum("customer_id").alias("s"), F.avg("customer_id").alias("a"), F.countDistinct("customer_id").alias("d"))
    ),
    "timestamps_utc": lambda: rows(
        spark.sql("SELECT to_timestamp('2026-03-29 01:30:00') AS t, date_format(to_timestamp('2026-03-29 01:30:00'), 'yyyy-MM-dd HH:mm EEE') AS f, unix_timestamp('2026-03-29 01:30:00') AS u")
    ),
    "union_by_name_missing": lambda: rows(
        customers.select("customer_id", "name").unionByName(orders.select("customer_id", "amount"), allowMissingColumns=True)
    ),
    "fillna_dropna": lambda: rows(orders.fillna({"amount": 0.0}).na.drop(subset=["customer_id"])),
    "row_number_latest": lambda: rows(
        orders.withColumn("rn", F.row_number().over(Window.partitionBy("customer_id").orderBy(F.col("ordered").desc()))).filter("rn = 1").drop("rn")
    ),
    "missing_column_error": lambda: rows(orders.select("no_such_column")),
    "parquet_roundtrip": lambda: (
        orders.write.mode("overwrite").parquet(str(WORK / "orders.parquet")),
        rows(spark.read.parquet(str(WORK / "orders.parquet"))),
    )[1],
    "split_explode": lambda: rows(
        spark.createDataFrame([(1, "a;b; c"), (2, None)], "id INT, tags STRING").select("id", F.explode_outer(F.split("tags", ";\\s*")).alias("tag"))
    ),
}

results = {"engine": ENGINE, "startup_s": round(startup, 3), "cases": {}}
for name, case in CASES.items():
    start = time.perf_counter()
    try:
        value = case()
    except Exception as e:  # record the failure as the result
        first = str(e).strip().splitlines()[0] if str(e).strip() else ""
        value = {"error": f"{type(e).__name__}: {first[:300]}"}
    value["seconds"] = round(time.perf_counter() - start, 3)
    results["cases"][name] = value

spark.stop()
if server is not None:
    server.stop()
results["total_s"] = round(time.perf_counter() - t0, 3)
OUT.write_text(json.dumps(results, indent=2), encoding="utf-8")
print(ENGINE, "startup", results["startup_s"], "total", results["total_s"])
