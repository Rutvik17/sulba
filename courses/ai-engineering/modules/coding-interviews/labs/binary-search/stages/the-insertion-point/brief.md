Write `insertion_point`, for a list of numbers sorted from smallest to largest:

```
insertion_point(numbers, value) -> the first position where value could go in numbers and
    keep it sorted
```

That's the position of the first number not smaller than `value`, or `len(numbers)` if every number is smaller. `insertion_point([1, 3, 3, 7, 9], 3)` returns `1`, and `insertion_point([1, 3, 3, 7, 9], 8)` returns `4`. Don't use the `bisect` module.

The tests' longest list has {% $fig.numbers %} numbers, searched {% $fig.searches %} times.
