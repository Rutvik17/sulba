A meeting is a pair `(start, end)` of times with `start < end`, and a room holds one meeting at a time. A meeting that ends frees its room for one that starts at the same time. Write `rooms_needed`:

```
rooms_needed(meetings) -> the fewest rooms that hold every meeting
```

`rooms_needed([(9, 10), (9, 12), (10, 11), (11, 13), (12, 14)])` returns `2`. No meetings need no rooms.

The tests' longest list has {% $fig.meetings %} meetings.
