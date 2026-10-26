```python
from collections import Counter


def least_time(tasks, cooldown):
    counts = Counter(tasks).values()
    most = max(counts, default=0)
    tied = sum(1 for count in counts if count == most)
    return max(len(tasks), (most - 1) * (cooldown + 1) + tied)
```

Laid out first, the commonest task's `most` runs need `cooldown` units after each but the last, so no schedule is shorter than `(most - 1) * (cooldown + 1)` units, plus one at the end for each task that also runs `most` times. A task that runs fewer than `most` times can put its runs one to a gap, filling the gaps in turn, and they stay `cooldown` apart. When the tasks more than fill the gaps, the gaps can widen to take them and no unit is idle, so the answer is the number of tasks. Counting the tasks takes time in proportion to how many there are.

Running the schedule a unit at a time, each unit choosing the free task with the most runs left, gives the same answer, but the longest test takes {% $fig.units %} units.
