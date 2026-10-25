Some of the month's records can't be taken at their word: a trip that ends before it begins, a fare below zero, a zone the city doesn't know. Dropping them would make every later count quietly smaller, so mark them instead, and let each count say what it leaves out. In `flags.py`, write `flagged(trips)`, the trips from your `trips(spark)` with a boolean column for each of these flags, after the trips' own columns and in this order, then `clean`, true when no flag is.

| Flag | True when |
| --- | --- |
| `outside_month` | the trip was picked up before 1 August 2025 or from 1 September |
| `backwards` | it was dropped off before it was picked up |
| `too_long` | it was dropped off more than 24 hours after it was picked up |
| `no_distance` | its distance is 0 or less |
| `negative` | its fare or its total is below 0 |
| `unknown_zone` | it was picked up or dropped off in zone 264 or 265, which the city's lookup marks as unknown and outside the city |

Each flag is true or false, never missing: a trip whose values don't show the problem, missing values included, isn't flagged. Then write `flag_counts(flagged)`, a dict of how many trips each flag marks, and how many are clean. Over the month, {% $fig.clean %} of the {% $fig.trips %} trips are clean.

```
flagged(trips) -> DataFrame
flag_counts(flagged) -> dict of name to int
```
