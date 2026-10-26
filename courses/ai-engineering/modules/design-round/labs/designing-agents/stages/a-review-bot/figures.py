from decimal import ROUND_HALF_UP, Decimal


def dollars(amount, places="0.01"):
    return f"${Decimal(amount).quantize(Decimal(places), rounding=ROUND_HALF_UP):,}"


def millions(tokens):
    if tokens < 1_000_000:
        return f"{tokens:,}"
    return f"{Decimal(tokens) / 1_000_000:,.1f}".removesuffix(".0") + " million"


def figures():
    prs = 600
    diff, context, output = 4_000, 8_000, 800
    price_in, price_out = Decimal("0.40"), Decimal("1.60")
    pr_in = diff + context
    day_in, day_out = prs * pr_in, prs * output
    # The checking call reads about as much again.
    day_cost = 2 * (day_in * price_in + day_out * price_out) / 1_000_000
    return {
        "engineers": "400",
        "prs": f"{prs:,}",
        "diff": f"{diff:,}",
        "context": f"{context:,}",
        "output": f"{output:,}",
        "price_in": dollars(price_in),
        "price_out": dollars(price_out),
        "pr_in": f"{pr_in:,}",
        "day_in": millions(day_in),
        "day_out": millions(day_out),
        "day_cost": dollars(day_cost),
        "max_comments": "5",
        "big_files": "120",
    }
