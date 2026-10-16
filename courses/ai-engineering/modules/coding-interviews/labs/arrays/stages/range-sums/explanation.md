```python
from itertools import accumulate


def range_sums(numbers, ranges):
    totals = [0, *accumulate(numbers)]
    return [totals[stop] - totals[start] for start, stop in ranges]
```

`totals[i]` is the sum of the first `i` numbers, a prefix sum, so a range's sum is the difference of two of them. One pass builds the prefix sums, and each range then takes one subtraction: the time grows with the length of the list plus the number of ranges, and the prefix sums take space in proportion to the list. The `0` at the start of `totals` lets a range from position `0`, and an empty range, work like any other.

Summing each slice instead takes up to one addition for each of {% $fig.numbers %} numbers in each of {% $fig.ranges %} ranges, {% $fig.additions %} in all, far past the time limit.
