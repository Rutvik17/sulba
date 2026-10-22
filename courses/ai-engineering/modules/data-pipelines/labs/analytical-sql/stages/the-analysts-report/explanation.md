A comparison with `NULL` gives `NULL`, not true or false, and `WHERE` keeps only the rows where its condition is true, so `borough <> 'EWR'` dropped every trip whose zone has no borough along with Newark's. `IS DISTINCT FROM` treats `NULL` as a value: in Postgres's documentation's words, "For non-null inputs, IS DISTINCT FROM is the same as the <> operator. However, if both inputs are null it returns false, and if only one input is null it returns true."

`count(*)` "computes the number of input rows", and `count(column)` "the number of input rows in which the input value is not null". Every aggregate but `count(*)` leaves out `NULL`s, which is what an average of the passengers that were reported needs, and what a count of trips doesn't. `coalesce` turned "not reported" into "no passengers", a different fact.

`BETWEEN` takes both its ends, so a day's report runs from its midnight to just before the next one: `>=` the day and `<` the next.
