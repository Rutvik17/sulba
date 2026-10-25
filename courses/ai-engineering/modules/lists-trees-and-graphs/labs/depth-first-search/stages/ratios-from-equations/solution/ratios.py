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
