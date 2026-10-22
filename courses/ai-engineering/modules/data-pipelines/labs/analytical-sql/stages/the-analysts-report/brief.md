The company's analyst had an assistant write the morning report's query before you started: `report.py`'s `boroughs(conn, day)`, a row for each pickup borough with its trips, its passengers per trip and its share of the day's trips. Newark Airport's trips are left out, since the company doesn't dispatch there. Its three tests all pass.

Review it as if tomorrow's report were about to go out: fix every problem you can find, and keep what it does right. Four hidden checks test it the way the report will use it. A run shows how many pass. You see which ones when you finish the review.

What the report must do:

- count every trip picked up on `day` but Newark's, once, in its pickup borough's row, with the trips from zones with no borough in a row whose borough is `None`;
- count a trip whether or not it reports its passengers;
- give passengers per trip over the trips that report them;
- leave the trips picked up at the next midnight to the next day's report.
