# The longest test, as tests/test_trade.py sets it: its prices, and the pairs of days they make.
PRICES = 100_000


def figures():
    return {"prices": f"{PRICES:,}", "pairs": f"{PRICES * (PRICES - 1) // 2:,}"}
