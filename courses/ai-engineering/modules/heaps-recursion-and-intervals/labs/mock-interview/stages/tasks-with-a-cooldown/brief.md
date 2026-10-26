A machine runs one task a unit of time, and each task is a letter. Two runs of the same task need at least `cooldown` units between them, and the machine can stand idle for a unit. Write `least_time`:

```
least_time(tasks, cooldown) -> the fewest units of time that run every task, in any order
```

`least_time(["A", "A", "A", "B", "B", "B"], 2)` returns 8: A, B, idle, A, B, idle, A, B. The tests' longest list has {% $fig.tasks %} tasks.
