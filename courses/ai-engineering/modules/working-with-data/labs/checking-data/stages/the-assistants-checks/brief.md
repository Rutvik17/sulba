The pipeline's checks were written by an assistant: `validate.py`, whose `validate` gives the problems that stop an extract, as messages. Its four tests all pass.

Review it as if next month's extract were about to arrive: fix every problem you can find, and keep what it does right. Four hidden production checks test it the way it will be used. A run shows how many pass. You see which ones when you finish the review.

What the checks must stop:

- a value a column doesn't allow, in any of its rows;
- a length of stay outside the inclusion criteria, or missing;
- an encounter id given to more than one row;
- an encounter after the patient's death, whichever discharge code records it.
