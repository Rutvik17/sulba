`spark.read.option("header", True).csv(WEATHER)` reads every column as a string. `F.split(F.col(f"{column}_ATTRIBUTES"), ",")[position]` takes one attribute, and `F.coalesce(..., F.lit(""))` turns a missing one into an empty string.

---

`F.trim(F.col(column)).cast("int") / 10` turns a padded value into a number of units. `F.when(attribute(column, 1) == "", value)` keeps it where the quality flag is blank and leaves it missing everywhere else.

---

`F.to_date("DATE")` gives the day, and `attribute("PRCP", 0) == "T"` whether only a trace fell. A weather type was seen where its column, trimmed, is `"1"`; `F.coalesce(..., F.lit(False))` makes an empty one false.
