Before your team started, an assistant wrote `estimate.py` for the office: `estimate(tasks, deadline)` simulates the project and gives the whole days within which four runs in five finish, and the share of runs that finish by the end of the deadline's day. It uses your `schedule.py`'s `Task` and `finish`. Its three tests all pass.

Review it as if the office were about to sign by it: fix every problem you can find, and keep what it does right. Four hidden checks test it the way the office will use it. A run shows how many pass. You see which ones when you finish the review.

What the code must do:

- draw each task's days from the triangular distribution of its low, likely and high days;
- draw each task apart from the others, so one running late says nothing of the rest;
- start each task once the tasks it waits for have ended, and run the tasks that don't wait for each other side by side;
- promise the fewest whole days by which at least four runs in five finish.

```
estimate(tasks, deadline, runs=10_000, seed=0) -> tuple[int, float]
```
