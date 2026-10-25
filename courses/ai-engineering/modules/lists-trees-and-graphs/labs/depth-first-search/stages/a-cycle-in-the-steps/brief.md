`needs` is a dict from each step of a job to the list of steps it needs done first. A step can be needed without a list of its own. Write `cycle`:

```
cycle(needs) -> a cycle of steps, each needing the next, as a list that starts and ends with
    the same step, or None when there's no cycle
```

`cycle({"a": ["b"], "b": ["c"], "c": ["a"]})` returns a list such as `["a", "b", "c", "a"]`, and `cycle({"a": ["b"], "b": []})` returns `None`. Any cycle will do. The tests' longest job has {% $fig.steps %} steps.
