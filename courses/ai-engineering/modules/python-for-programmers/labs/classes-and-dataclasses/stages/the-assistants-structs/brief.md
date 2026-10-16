The service needs more than the port has: enums for a sample's side, the clinic's own message for a field where it has written one, and unions joined with a bar. The clinic asked an assistant for them, and the assistant wrote `service.py`, with structs of its own. Its five tests all pass.

Review it as if the service were about to check the day's samples with it: fix every problem you can find, and keep what it does right. Four hidden production checks test it the way the service will use it. A run shows how many pass. You see which ones when you finish the review.

What the code must do:

- keep each enums' options to itself;
- fail a value with the clinic's message wherever a struct was given one;
- give failures the daily report can count, with `collections.Counter`;
- leave a union as it was when it's joined into a wider one.
