```python
from bisect import bisect_right


class Calendar:
    def __init__(self):
        self.starts = []
        self.ends = []

    def book(self, start, end):
        place = bisect_right(self.starts, start)
        if place > 0 and self.ends[place - 1] > start:
            return False
        if place < len(self.starts) and self.starts[place] < end:
            return False
        self.starts.insert(place, start)
        self.ends.insert(place, end)
        return True
```

The bookings don't overlap, so sorted by start they're sorted by end too. A new booking can only overlap its neighbours there: the one before, if it ends after the new start, and the one after, if it starts before the new end. `bisect_right` finds that place in time in proportion to the logarithm of the bookings, and `insert` puts the new booking's start and end in their lists at it.

Comparing a new booking with every booking so far is the slow way: up to {% $fig.comparisons %} comparisons for the longest test's {% $fig.bookings %} bookings.
