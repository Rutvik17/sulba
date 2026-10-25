```python
def ratios(equations, queries):
    links = {}
    for top, bottom, value in equations:
        links.setdefault(top, []).append((bottom, 1 / value))
        links.setdefault(bottom, []).append((top, value))
    root, scale = {}, {}
    for start in links:
        if start in root:
            continue
        root[start], scale[start] = start, 1.0
        stack = [start]
        while stack:
            name = stack.pop()
            for other, factor in links[name]:
                if other not in root:
                    root[other] = start
                    scale[other] = scale[name] * factor
                    stack.append(other)
    found = []
    for top, bottom in queries:
        if top in root and bottom in root and root[top] == root[bottom]:
            found.append(scale[top] / scale[bottom])
        else:
            found.append(None)
    return found
```

Each equation is an edge between two variables, `top / bottom` one way and its inverse the other, and multiplying along a path from x to y gives x / y. A search for each query would walk a whole group each time, so instead one search per group gives each variable its value over the group's first variable, its root, and a query within one group is the ratio of its two values: $\frac{top / root}{bottom / root}$. Each equation is followed twice and each query answered in one step.

Searching from the top variable for each query is the slow way: up to {% $fig.walks %} steps for the longest test's queries along its chain of variables.
