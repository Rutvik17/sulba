The clinic asked an assistant to type the service's intake, and the assistant wrote `intake.py`: `take`, which checks each record coming in, `label` and `note_of` for the day's report, and `is_radius`. Its four tests all pass, `mypy --strict` among them.

Review it as if the service were about to take a day's records with it: fix every problem you can find, and keep what it does right. Four hidden production checks test it the way the service will use it. A run shows how many pass. You see which ones when you finish the review.

What the code must do:

- let mypy catch a caller's mistakes;
- take only records a `Sample` can hold;
- give every sample's note as text;
- take every radius above zero, written as an int or a float.
