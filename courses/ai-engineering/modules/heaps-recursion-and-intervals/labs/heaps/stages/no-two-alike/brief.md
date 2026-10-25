Write `reorganized`:

```
reorganized(text) -> the text's letters in an order where no two alike stand side by side,
    or "" when no order is like that
```

`reorganized("aab")` returns `"aba"`, and `reorganized("aaab")` returns `""`. Any order that keeps alike letters apart will do. The tests' longest text has {% $fig.letters %} letters.
