A list whose last node points back to an earlier one never ends: walking it runs round a cycle. Write `cycle_start`:

```
cycle_start(head) -> the first node of the cycle the list runs into, or None if it ends
```

For `1 → 2 → 3 → 4`, with 4 pointing back to 2, `cycle_start` returns the node holding 2. It changes no node, and it uses no more than a few names of extra space: no set or dict of the nodes it has seen.

The tests' longest list has {% $fig.nodes %} nodes.
