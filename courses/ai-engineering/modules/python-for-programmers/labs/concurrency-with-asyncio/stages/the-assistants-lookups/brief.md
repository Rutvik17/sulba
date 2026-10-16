The clinic asked an assistant for the lookups of the service's daily run, and the assistant wrote `day_lookups.py`, with a registry stand-in of its own: `check_code` for one code, and `check_limited`, `check_each` and `check_in_time` for a day's codes. Its four tests all pass.

Review it as if the service were about to check a day's codes against the registry with it: fix every problem you can find, and keep what it does right. Four hidden production checks test it the way the service will use it. A run shows how many pass. You see which ones when you finish the review.

What the code must do:

- fail a code the registry doesn't know;
- keep to its limit when lookups fail;
- keep a lookup that couldn't reach the registry to its own code;
- time out a slow lookup without the others.
