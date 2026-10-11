def mean(values):
    return sum(values) / len(values)


def middle(values):
    ordered = sorted(values)
    return ordered[len(ordered) // 2]
