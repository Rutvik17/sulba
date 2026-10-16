Write `dedupe`, for a list of numbers sorted from smallest to largest:

```
dedupe(numbers) -> moves each different value of numbers, in order, to its front, and returns
    how many different values there are
```

```python
numbers = [1, 1, 2, 3, 3, 3, 7]
dedupe(numbers)  # 4
numbers[:4]  # [1, 2, 3, 7]
```

Change the list itself, with no second list. The tests check the values before the count, and ignore what comes after. The tests' longest list has {% $fig.numbers %} numbers.
