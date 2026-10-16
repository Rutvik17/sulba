Write `zero_triples`:

```
zero_triples(numbers) -> every different triple (a, b, c) of numbers at three different positions
    that adds up to 0, each with a <= b <= c, in sorted order
```

```python
zero_triples([-3, 1, 2, -1, 0, 2, -2, 1])
# [(-3, 1, 2), (-2, 0, 2), (-2, 1, 1), (-1, 0, 1)]
```

A triple appears once however many ways the numbers make it, and a number used twice in a triple, like the `1` in `(-2, 1, 1)`, must appear twice in the list. The tests' longest list has {% $fig.numbers %} numbers.
