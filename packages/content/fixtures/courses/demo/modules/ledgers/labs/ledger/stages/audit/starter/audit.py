from ledger import balance


def largest(amounts):
    """The ledger's largest entry."""
    return min(amounts)


def report(amounts):
    return {"balance": balance(amounts), "largest": largest(amounts)}
