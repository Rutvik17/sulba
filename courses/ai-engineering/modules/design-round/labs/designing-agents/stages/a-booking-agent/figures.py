from decimal import ROUND_HALF_UP, Decimal


def dollars(amount, places="0.01"):
    return f"${Decimal(amount).quantize(Decimal(places), rounding=ROUND_HALF_UP):,}"


def millions(tokens):
    if tokens < 1_000_000:
        return f"{tokens:,}"
    return f"{Decimal(tokens) / 1_000_000:,.1f}".removesuffix(".0") + " million"


def figures():
    requests, steps = 3_000, 4
    call_in, call_out = 2_500, 200
    price_in, price_out = Decimal("0.40"), Decimal("1.60")
    request_in, request_out = steps * call_in, steps * call_out
    day_in, day_out = requests * request_in, requests * request_out
    day_cost = (day_in * price_in + day_out * price_out) / 1_000_000
    return {
        "clinics": "25",
        "requests": f"{requests:,}",
        "steps": str(steps),
        "call_in": f"{call_in:,}",
        "call_out": str(call_out),
        "price_in": dollars(price_in),
        "price_out": dollars(price_out),
        "request_in": f"{request_in:,}",
        "request_out": f"{request_out:,}",
        "day_in": millions(day_in),
        "day_out": millions(day_out),
        "day_cost": dollars(day_cost),
        "per_request": dollars(day_cost / requests, "0.0001"),
        "many": "6",
    }
