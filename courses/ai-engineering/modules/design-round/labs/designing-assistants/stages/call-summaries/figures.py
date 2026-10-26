from decimal import ROUND_HALF_UP, Decimal


def dollars(amount, places="0.01"):
    return f"${Decimal(amount).quantize(Decimal(places), rounding=ROUND_HALF_UP):,}"


def millions(tokens):
    return f"{Decimal(tokens) / 1_000_000:,.1f}".removesuffix(".0") + " million"


def figures():
    calls, hours = 30_000, 12
    transcript, instructions, summary = 2_000, 500, 250
    price_in, price_out = Decimal("0.40"), Decimal("1.60")
    outage_hours = 2
    call_in = transcript + instructions
    day_in, day_out = calls * call_in, calls * summary
    day_cost = (day_in * price_in + day_out * price_out) / 1_000_000
    per_hour = calls // hours
    backlog = per_hour * outage_hours
    # In the hour after the outage the workers take that hour's calls and the backlog.
    clear_rate = Decimal(per_hour + backlog) / 3600
    return {
        "calls": f"{calls:,}",
        "hours": str(hours),
        "transcript": f"{transcript:,}",
        "instructions": str(instructions),
        "summary": str(summary),
        "price_in": dollars(price_in),
        "price_out": dollars(price_out),
        "call_in": f"{call_in:,}",
        "day_in": millions(day_in),
        "day_out": millions(day_out),
        "day_cost": dollars(day_cost),
        "per_hour": f"{per_hour:,}",
        "rate": f"{Decimal(per_hour) / 3600:.1f}",
        "backlog": f"{backlog:,}",
        "clear_rate": f"{clear_rate:.1f}",
        "sample": "200",
    }
