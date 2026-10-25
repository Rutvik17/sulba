The dispatcher's analyst had an assistant build the daily table in one go before you started: `daily_table.py`'s `daily_table(spark)`, a row for each day of August and each borough, with the day's weekday, the borough's clean pickups, the day's rain and high, and whether it was wet. It reads the weather and the zones itself, takes the trips from `trips.py` and `flags.py`, and its three tests all pass.

Review it as if the table were about to answer the dispatcher's question: fix every problem you can find, and keep what it does right. Four hidden checks test it the way the table will be used. A run shows how many pass. You see which ones when you finish the review.

What the table must do:

- leave out a value that failed a quality check, and keep a trace of rain as 0 mm;
- count every clean trip, whatever else its record leaves out;
- give each day the weekday the calendar gives it;
- give every borough a row on every day, with 0 trips on a day it had none.
