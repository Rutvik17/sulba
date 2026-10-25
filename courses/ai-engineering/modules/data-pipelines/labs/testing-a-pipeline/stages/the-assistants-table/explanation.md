NCEI's data service gives each value's attributes in one string, its documentation's example being "T,,0,0700": the measurement flag first, then the quality flag. A position in that string is easy to get wrong and hard to see in the output, since a trace day missing its rain looks like a day the station missed.

`F.count` of a column is "the number of items in a group" that aren't missing: its documentation's second example is to "Count non-null values in a specific column". `F.count("*")` counts the rows. Counting a column says how many rows report it, which is a different question.

`dayofweek` gives the day of the week "as integer", which "Ranges from 1 for a Sunday through to 7 for a Saturday". A list of names indexed by it has to start where it does, and `date_format` with the pattern `EEEE` gives the name without one.

A join's `how` is "default inner", which keeps only the rows that match. The grid of days and boroughs was right, and so was the `coalesce`: an inner join to the counts undid both, and a left join keeps every row of the grid.
