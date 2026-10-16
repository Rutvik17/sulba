```python
import operator

OPERATORS = {
    "+": operator.add,
    "-": operator.sub,
    "*": operator.mul,
    "//": operator.floordiv,
}


def evaluate(tokens):
    stack = []
    for token in tokens:
        if token in OPERATORS:
            right = stack.pop()
            left = stack.pop()
            stack.append(OPERATORS[token](left, right))
        else:
            stack.append(int(token))
    return stack.pop()
```

A number waits on the stack until an operator uses it, and an operator always combines the two most recent values that are still waiting, so the stack holds exactly what each operator needs. Popping the right-hand value first keeps `-` and `//` the right way round. A token is an operator only when it is one exactly, so `"-7"` is read as a number. Each token is handled once: time in proportion to the expression, and space for the values waiting.

Finding the first operator, replacing it and its two values with the result, and starting again from the beginning reads the numbers before the first operator again after every operator. The longest test has {% $fig.numbers %} numbers and then {% $fig.operators %} operators, so that's {% $fig.reads %} tokens read, far past the time limit.
