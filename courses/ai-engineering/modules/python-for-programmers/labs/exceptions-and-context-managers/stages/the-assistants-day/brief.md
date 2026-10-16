The service's daily run checks each export with the assistant's `daily.py`: `parse_line`, `check_day` and `report` as yours are, with structs of its own, and a `Batch` that tells a broken struct apart from a record that fails. Its five tests all pass.

Review it as if the service were about to check the day's exports with it: fix every problem you can find, and keep what it does right. Four hidden production checks test it the way the service will use it. A run shows how many pass. You see which ones when you finish the review.

What the code must do:

- keep a failed line's error in its batch, and go on to the next line;
- let an error of the block's own go on, as it was;
- keep json's error as the cause of a line that isn't JSON;
- log each record that fails, and let every other error of the day reach the caller.
