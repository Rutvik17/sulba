```python
def symbol(row, place):
    if row == 1:
        return 0
    parent = symbol(row - 1, (place + 1) // 2)
    return parent if place % 2 else 1 - parent
```

Each symbol is written as two in the next row, the first the same and the second flipped. So the symbol at a place comes from place `(place + 1) // 2` of the row before, flipped when the place is even, and the recursion climbs a row a call: {% $fig.rows %} calls for row {% $fig.rows %}, whatever the place.

Climbing a row drops the last binary digit of `place - 1`, and the symbol flips when that digit is 1. So the symbol is also how many 1s `place - 1` has in binary, taken mod 2: `bin(place - 1).count("1") % 2`.

Writing out the rows down to the one asked is the slow way: row {% $fig.rows %} alone has {% $fig.length %} symbols.
