Write `balanced`:

```
balanced(text) -> whether every bracket in text is closed by its own kind, in the right order
```

The brackets are `()`, `[]` and `{}`, and every other character is ignored. `balanced("{[a](b)}")` returns `True`, and `balanced("([)]")` and `balanced("((")` return `False`. A text with no brackets is balanced.

The tests' longest text has {% $fig.characters %} characters.
