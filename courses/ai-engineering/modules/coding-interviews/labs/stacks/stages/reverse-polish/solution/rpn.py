import operator

OPERATORS = {
    "+": operator.add,
    "-": operator.sub,
    "*": operator.mul,
    "//": operator.floordiv,
}


def evaluate(tokens):
    """The value of the expression the tokens write in reverse Polish notation."""
    stack = []
    for token in tokens:
        if token in OPERATORS:
            right = stack.pop()
            left = stack.pop()
            stack.append(OPERATORS[token](left, right))
        else:
            stack.append(int(token))
    return stack.pop()
