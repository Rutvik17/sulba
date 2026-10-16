Write `first_and_last`, for a list of numbers sorted from smallest to largest:

```
first_and_last(numbers, value) -> the first and last positions of value in numbers, or None if
    it isn't there
```

`first_and_last([2, 4, 4, 4, 6, 8], 4)` returns `(1, 3)`, and `first_and_last([2, 4, 4, 4, 6, 8], 5)` returns `None`. Don't use the `bisect` module.

The tests' longest list has {% $fig.numbers %} numbers in runs of {% $fig.run %} equal ones, searched {% $fig.searches %} times.
