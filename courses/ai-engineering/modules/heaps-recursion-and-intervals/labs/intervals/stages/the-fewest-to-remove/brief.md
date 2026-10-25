`meetings` is a list of meetings `(start, end)`, each from its start up to its end, with `start < end`, in any order. A meeting that ends at 10 and one that starts at 10 don't overlap. Write `fewest_removed`:

```
fewest_removed(meetings) -> the fewest meetings to remove so that no two of the rest overlap
```

`fewest_removed([(1, 2), (2, 3), (3, 4), (1, 3)])` returns 1: removing `(1, 3)` leaves three that don't overlap. The tests' longest list has {% $fig.meetings %} meetings.
