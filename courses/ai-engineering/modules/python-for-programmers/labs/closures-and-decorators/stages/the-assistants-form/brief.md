The form's spec lists each measurement with its range, and the clinic asked an assistant for the code that builds the form's checks from it. The assistant wrote `form.py`: `build` makes a counted check for each measurement, with `counted`, `enums` and `refine` of its own. Its five tests all pass.

Review it as if the service were about to check the form's records with it: fix every problem you can find, and keep what it does right. Four hidden production checks test it the way the service will use it. A run shows how many pass. You see which ones when you finish the review.

What the code must do:

- give each field its own range;
- keep each check's name, which the service's log shows beside each failure;
- keep the options a check was made with;
- report a value of the wrong kind, never raise an error for it.
