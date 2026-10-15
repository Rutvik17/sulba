The analysts send the network a report each month: patients and readmissions by admission source. They asked an assistant for the code, and the assistant wrote `monthly.py`: `report`, which reads the extract and the mapping and gives a row for each admission source, then one for all of them. Its four tests all pass.

Review it as if this month's report were about to go out: fix every problem you can find, and keep what it does right. Four hidden production checks test it the way it will be used. A run shows how many pass. You see which ones when you finish the review.

The analysts' request:

- Each patient once, at their first encounter, without deaths and hospice care.
- Each admission source by its description in the mapping, with the sources that stand for unknown, and any source the mapping lacks, together as `Unknown`.
- For each row, its patients, those readmitted within {% $fig.days %} days and their share.
- A last row, `All sources`, for every patient.
