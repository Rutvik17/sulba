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
