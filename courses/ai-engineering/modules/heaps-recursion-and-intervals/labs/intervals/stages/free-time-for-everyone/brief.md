`schedules` is a list of people's schedules, each a list of their busy times `(start, end)`, sorted, from each start up to its end, none of one person's overlapping. Write `free_time`:

```
free_time(schedules) -> the times when no one is busy, between the earliest start and the
    latest end, sorted
```

`free_time([[(1, 2), (5, 6)], [(1, 3)], [(4, 10)]])` returns `[(3, 4)]`. A time when one person's busy time ends and another's starts isn't free. The tests' longest set of schedules has {% $fig.people %} people with {% $fig.each %} busy times each.
