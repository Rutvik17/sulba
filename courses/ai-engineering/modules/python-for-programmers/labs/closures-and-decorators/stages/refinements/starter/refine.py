def refine(check, name, test):
    """A check that passes what check passes when test(value) is True. test can give a
    message of its own in place of False."""
    raise NotImplementedError


def min_(check, threshold, exclusive=False):
    """A check that passes what check passes when it's at least threshold, or more than
    threshold when exclusive."""
    raise NotImplementedError


def max_(check, threshold, exclusive=False):
    """A check that passes what check passes when it's at most threshold, or less than
    threshold when exclusive."""
    raise NotImplementedError


def pattern(check, regex):
    """A check that passes what check passes when regex matches somewhere in it."""
    raise NotImplementedError
