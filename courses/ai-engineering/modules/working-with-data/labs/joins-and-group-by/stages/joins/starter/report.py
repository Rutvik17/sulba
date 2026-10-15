def describe(table, mapping):
    """A copy of table with each code column's descriptions beside it, every encounter kept
    once, in its order."""
    raise NotImplementedError


def unmatched(table, mapping):
    """For each code column, the codes in table that the mapping lacks, smallest first."""
    raise NotImplementedError
