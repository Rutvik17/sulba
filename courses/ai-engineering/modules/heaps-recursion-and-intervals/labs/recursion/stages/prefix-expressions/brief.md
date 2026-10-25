An expression is a whole number, such as `42` or `-7`, or an operator and its operands in parentheses, such as `(+ 1 2 3)`, where each operand is an expression too. `+` adds its operands and `*` multiplies them, and `-` takes the rest from the first, or negates an operand on its own. Write `evaluate`:

```
evaluate(expression) -> the expression's value, a whole number
```

`evaluate("(+ 1 (* 2 3) 4)")` returns 11, and `evaluate("(- (* 2 5) 3 (- 1))")` returns 8. Spaces, one or more, separate the parts, and a parenthesis needs none: `(*(+ 1 2)(- 4 1))` is 9. The tests' longest expression has {% $fig.chars %} characters, and their deepest has parentheses {% $fig.depth %} levels deep.
