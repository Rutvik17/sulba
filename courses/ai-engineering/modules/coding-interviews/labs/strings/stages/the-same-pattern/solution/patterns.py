def same_pattern(first, second):
    """Whether renaming first's characters, one to one, can turn it into second."""
    if len(first) != len(second):
        return False
    forward, backward = {}, {}
    for a, b in zip(first, second):
        if forward.setdefault(a, b) != b or backward.setdefault(b, a) != a:
            return False
    return True
