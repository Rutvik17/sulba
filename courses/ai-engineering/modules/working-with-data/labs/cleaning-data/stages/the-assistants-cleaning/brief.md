The network's analysts want the whole cleaning in one function before they count anything, and asked an assistant for it. The assistant wrote `clean.py`: `clean`, which reads the extract and gives each patient's first encounter, without deaths and hospice care, with the codes for unknown read as missing and `readmitted` as `True` or `False`. Its five tests all pass.

Review it as if the analysts were about to count readmissions with it: fix every problem you can find, and keep what it does right. Four hidden production checks test it the way it will be used. A run shows how many pass. You see which ones when you finish the review.

The analysts' request:

- Each `?` read as missing, and no other value: a `None` in `A1Cresult` or `max_glu_serum` is a test not done.
- The codes for unknown, and a gender of `Unknown/Invalid`, read as missing.
- Each patient's first encounter, the one with the lowest `encounter_id`, whatever order the extract arrives in.
- No encounter that ended in death or hospice care.
- `readmitted` `True` for a readmission within {% $fig.days %} days, and `False` for the rest.
