```python
def survivor(people, step):
    place = 0
    for size in range(2, people + 1):
        place = (place + step) % size
    return place + 1
```

When person `step` leaves, the circle is `people - 1` people, counted from the next person, so its survivor is the smaller circle's, `step` places further on. Counting places from 0, that's $J(n) = (J(n - 1) + \text{step}) \bmod n$, with $J(1) = 0$, and the loop works it out from a circle of 2 up to the whole circle, one step per person.

Written as a function that calls itself for `n - 1`, the same rule goes a call deep per person, and Python stops it long before {% $fig.people %}: its recursion limit is "the maximum depth of the Python interpreter stack", and going past it raises `RecursionError`. The `sys` documentation says the limit "prevents infinite recursion from causing an overflow of the C stack and crashing Python", and that raising it "should be done with care, because a too-high limit can lead to a crash." A recursion that only ever calls itself once, for the next smaller case, is a loop.

Keeping the circle in a list and popping each person who leaves is the slow way: each pop moves the people after it along, up to {% $fig.people %} of them, for each of the {% $fig.leave %} who leave.
