`union` "resolves columns by position (not by name)", in its documentation's words, and a `select` that keeps each file's columns in the file's own order gives two orders. `unionByName` matches them by name, which is what two files of the same records but different layouts need.

`F.count` is "the number of items in a group", the values that aren't missing: its documentation's own example counts the non-null values in a column. `F.when` returns null "If pyspark.sql.Column.otherwise() is not invoked", so `F.count(F.when(condition, 1))` would have counted the card trips, and `.otherwise(0)` turned every other trip into a value to count. `F.count_if` "Returns the number of TRUE values" and says what it means.

Spark's arithmetic is null intolerant: such expressions "return NULL when one or more arguments of expression are NULL". Aggregates go the other way: "NULL values are ignored from processing by all the aggregate functions." So `sum(a + b)` drops a row's `b` whenever its `a` is missing, and `sum(a) + sum(b)` keeps every value each column has.

`dayofmonth` extracts "the day of the month of a given date/timestamp as integer" and nothing about the month, so a report of August's days keeps August's trips first.
