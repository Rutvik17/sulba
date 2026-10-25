```python
def evaluate(expression):
    tokens = expression.replace("(", " ( ").replace(")", " ) ").split()
    place = 0

    def read():
        nonlocal place
        token = tokens[place]
        place += 1
        if token != "(":
            return int(token)
        operator = tokens[place]
        place += 1
        values = []
        while tokens[place] != ")":
            values.append(read())
        place += 1
        if operator == "+":
            return sum(values)
        if operator == "*":
            product = 1
            for value in values:
                product *= value
            return product
        if len(values) == 1:
            return -values[0]
        return values[0] - sum(values[1:])

    return read()
```

Reading an expression is the same job at every level: a number is read as it is, and a parenthesis starts an operator and its operands, each an expression, up to the matching `)`. So `read` calls itself for each operand, and `place`, shared through `nonlocal`, moves along the parts as each is used. Each part is read once, so the time is in proportion to the expression's length, and the calls go as deep as the parentheses: {% $fig.depth %} levels for the tests' deepest.

Working out the innermost parentheses and writing each value back into the text is the slow way: the tests' longest expression has {% $fig.groups %} of them, each a pass over the text, which starts at {% $fig.chars %} characters.
