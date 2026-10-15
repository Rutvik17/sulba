def mark_unknown(table):
    """A copy of table with each code or value that stands for unknown read as missing, and
    the code columns kept as whole numbers."""
    raise NotImplementedError


def drop_sparse(table, limit):
    """A copy of table without the columns whose share of missing values is over limit."""
    raise NotImplementedError
