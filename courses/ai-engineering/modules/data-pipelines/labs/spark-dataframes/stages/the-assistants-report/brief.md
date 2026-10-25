The dispatcher's analyst had an assistant write the month's report before you started: `report.py`'s `daily_report(spark)`, a row for each service on each day of August with its trips, the trips paid by card, its fares, tips and takings, and the congestion charges collected, the congestion surcharge and the CBD congestion fee together. It reads the two files itself, and its three tests all pass.

Review it as if the report were about to go to the company's owners: fix every problem you can find, and keep what it does right. Four hidden checks test it the way the report will be used. A run shows how many pass. You see which ones when you finish the review.

What the report must do:

- give each service's own amounts, from its own file's columns;
- count as card trips only the trips paid by card, `payment_type` 1;
- count every charge a trip reports, even when it reports another as missing;
- count each trip in the day of August it was picked up, and no trip from another month.
