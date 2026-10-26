from decimal import ROUND_HALF_UP, Decimal


def dollars(amount):
    return f"${Decimal(amount).quantize(Decimal('1'), rounding=ROUND_HALF_UP):,}"


def figures():
    month_bill = Decimal(90_000)
    repeat_share = Decimal("0.25")
    return {
        "teams": "14",
        "month_bill": dollars(month_bill),
        "calls_day": "2,000,000",
        "peak_rps": "120",
        "repeat_share": f"{repeat_share:.0%}",
        "cache_saving": dollars(month_bill * repeat_share),
        "overhead_ms": "10",
    }
