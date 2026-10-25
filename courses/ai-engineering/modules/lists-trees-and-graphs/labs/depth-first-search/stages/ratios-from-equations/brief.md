Each of `equations` is `(top, bottom, value)`, meaning that `top / bottom` is `value`, for variables named by strings, every value positive. Write `ratios`:

```
ratios(equations, queries) -> for each query (top, bottom), top / bottom, or None when the
    equations don't settle it
```

`ratios([("a", "b", 2.0), ("b", "c", 3.0)], [("a", "c"), ("b", "a"), ("a", "e"), ("a", "a"), ("x", "x")])` returns `[6.0, 0.5, None, 1.0, None]`: `e` and `x` are in no equation. The tests' longest lists have {% $fig.equations %} equations and {% $fig.queries %} queries.
