from ledger import balance


def close(amounts):
    return {"balance": balance(amounts), "entries": len(amounts)}
