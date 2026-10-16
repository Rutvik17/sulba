```python
def days_until_warmer(temperatures):
    waits = [0] * len(temperatures)
    waiting = []
    for day, temperature in enumerate(temperatures):
        while waiting and temperatures[waiting[-1]] < temperature:
            earlier = waiting.pop()
            waits[earlier] = day - earlier
        waiting.append(day)
    return waits
```

`waiting` holds the days that haven't seen a warmer day yet. A day colder than one below it on the stack would have settled it, so their temperatures never rise towards the top, and a new day settles the colder ones from the top down, stopping at the first that isn't colder. Days left waiting at the end keep a wait of `0`. Each day is pushed once and popped at most once: time in proportion to the list, and space for the days waiting.

Searching ahead from each day for a warmer one reads up to {% $fig.reads %} days for the longest test's {% $fig.days %}, which cool day by day until a warm last day, far past the time limit.
