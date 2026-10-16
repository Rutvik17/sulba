A list of different numbers was sorted, then rotated: some numbers from its front moved, in order, to its back. Write `rotated_search`:

```
rotated_search(numbers, value) -> the position of value in numbers, or None if it isn't there
```

`rotated_search([15, 18, 22, 3, 7, 11], 7)` returns `4`. A list can be rotated by none of its numbers, and so be sorted.

The tests' longest list has {% $fig.numbers %} numbers, searched {% $fig.searches %} times. Each search must take time in proportion to `$\log n$`.
