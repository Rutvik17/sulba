Each of `streams` is an iterable of numbers in order, and some may never end. Write `merged`:

```
merged(streams) -> an iterator of every item of the streams, in order, reading each stream
    only as far as it needs to give the next item
```

`list(merged([[1, 4, 5], [1, 3, 4], [2, 6]]))` gives `[1, 1, 2, 3, 4, 4, 5, 6]`, and the first items of `merged([itertools.count(0, 2), itertools.count(1, 2)])` are 0, 1, 2, 3 and on. A stream may be empty. The tests take the first {% $fig.items %} items of {% $fig.streams %} streams that never end.
