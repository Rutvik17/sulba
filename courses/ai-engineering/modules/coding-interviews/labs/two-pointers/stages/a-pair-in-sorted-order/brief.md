Write `sorted_pair`, for a list of numbers sorted from smallest to largest:

```
sorted_pair(numbers, target) -> the positions (i, j), with i < j, of two numbers that add up to
    target, or None if no two do
```

`sorted_pair([1, 3, 4, 6, 9, 11], 13)` returns `(2, 4)`. A number can't pair with itself, and when several pairs add up to the target, return any one of them.

Use no space besides a few variables: no dict, no set and no second list. The tests' longest list has {% $fig.numbers %} numbers.
