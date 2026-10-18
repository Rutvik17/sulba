from ledger import balance


def largest(amounts):
    """The ledger's largest entry."""
    return max(amounts)


def report(amounts):
    return {"balance": balance(amounts), "largest": largest(amounts)}
