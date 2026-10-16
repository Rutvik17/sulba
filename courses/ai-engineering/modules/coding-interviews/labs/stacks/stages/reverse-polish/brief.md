In reverse Polish notation, an operator follows the two values it combines, so `7 2 - 3 *` is `(7 - 2) * 3`. Write `evaluate`:

```
evaluate(tokens) -> the value of the expression the tokens write in reverse Polish notation
```

`evaluate(["7", "2", "-", "3", "*"])` returns `15`, and `evaluate(["4", "13", "5", "//", "+"])` returns `6`. A token is an integer, such as `"-7"`, or one of the operators `"+"`, `"-"`, `"*"` and `"//"`, which divides as Python's `//` does: `evaluate(["-7", "2", "//"])` returns `-4`. Each expression in the tests is well formed and never divides by zero.

The tests' longest expression has {% $fig.tokens %} tokens.
