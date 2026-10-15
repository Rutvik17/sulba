The network's dashboard shows a report of readmissions by admission source, and the analysts asked an assistant for its SQL. The assistant wrote `dashboard.py`: `report`, which asks the database for a row for each admission source, then one for all of them. Its four tests all pass.

Review it as if this month's report were about to go out: fix every problem you can find, and keep what it does right. Four hidden production checks test it the way it will be used. A run shows how many pass. You see which ones when you finish the review.

The analysts' request:

- Each patient once, at their first encounter, without deaths and hospice care.
- None of the patients in `opted_out`, the privacy team's table of patients who asked not to be counted.
- Each admission source by its description in `codes`, with the sources that stand for unknown, and any source the mapping lacks, together as `Unknown`.
- For each row, its patients, those readmitted within {% $fig.days %} days and their share, then a last row, `All sources`, for every patient.
