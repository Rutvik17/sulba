An office's computers are numbered from 1 to `n`, and `n` cables join them in pairs, `(a, b)`, each joining two different computers. The office wired its computers as a tree, every computer joined to every other by exactly one way along the cables, and then added one cable too many, so the cables make one loop. Write `extra_cable`:

```
extra_cable(cables) -> the cable to take out, so the rest join every computer with no loop;
    of the cables that would do, the one latest in the list
```

For `[(1, 2), (1, 3), (2, 3)]`, any of the three would do, and the answer is `(2, 3)`, the last. For `[(1, 2), (2, 3), (3, 4), (1, 4), (1, 5)]`, it's `(1, 4)`. The tests' largest office has {% $fig.computers %} computers.
