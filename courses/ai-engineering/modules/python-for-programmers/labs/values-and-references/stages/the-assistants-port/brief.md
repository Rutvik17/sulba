The clinic wants the service's checks in one module, and asked an assistant to port them. The assistant wrote `intake.py`: `number`, `literal`, `enums`, `with_defaults` and `known_fields`. Its five tests all pass.

Review it as if the service were about to check the form's records with it: fix every problem you can find, and keep what it does right. Four hidden production checks test it the way the service will use it. A run shows how many pass. You see which ones when you finish the review.

What the code must do:

- compare values as JavaScript's `===` does, whatever object holds them, such as a value `json.loads` has just read;
- never take a boolean for a number;
- fill in only the fields a record leaves out;
- leave the record it's given as it was.
