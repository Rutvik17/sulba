`spark.read.parquet(path)` reads a file as a DataFrame, and its times come as `timestamp_ntz`, a time on New York's clocks with no time zone. Read each file the same way: a function of the path, the service and the times' prefix.

---

`select` makes the new columns: `F.lit("yellow").alias("service")` for the service, and `F.col("VendorID").cast("int").alias("vendor")` for each column the file has, where `F` is `pyspark.sql.functions`. A list of each column's name, type and source keeps the two files in step.

---

Join the two with `unionByName`, which matches the columns by their names, so the order each `select` gives them can't send a value to the wrong column.
