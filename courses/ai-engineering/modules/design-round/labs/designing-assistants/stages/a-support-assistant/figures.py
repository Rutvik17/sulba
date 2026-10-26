from decimal import ROUND_HALF_UP, Decimal


def dollars(amount, places="0.01"):
    return f"${Decimal(amount).quantize(Decimal(places), rounding=ROUND_HALF_UP):,}"


def millions(tokens):
    return f"{Decimal(tokens) / 1_000_000:,.1f}".removesuffix(".0") + " million"


def figures():
    questions = 12_000
    answerable = Decimal("0.7")
    peak_share = Decimal("0.12")
    tokens_in, tokens_out = 3_000, 300
    price_in, price_out = Decimal("0.40"), Decimal("1.60")
    month_days = 30
    day_in, day_out = questions * tokens_in, questions * tokens_out
    cost_in = day_in * price_in / 1_000_000
    cost_out = day_out * price_out / 1_000_000
    day_cost = cost_in + cost_out
    peak_hour = questions * peak_share
    return {
        "questions": f"{questions:,}",
        "pages": "300",
        "answerable": f"{answerable:.0%}",
        "answered": f"{int(questions * answerable):,}",
        "to_staff": f"{int(questions * (1 - answerable)):,}",
        "peak_share": f"{peak_share:.0%}",
        "tokens_in": f"{tokens_in:,}",
        "tokens_out": f"{tokens_out:,}",
        "price_in": dollars(price_in),
        "price_out": dollars(price_out),
        "peak_hour": f"{int(peak_hour):,}",
        "peak_rate": f"{peak_hour / 3600:.1f}",
        "day_in": millions(day_in),
        "day_out": millions(day_out),
        "cost_in": dollars(cost_in),
        "cost_out": dollars(cost_out),
        "day_cost": dollars(day_cost),
        "month_days": str(month_days),
        "month_cost": dollars(day_cost * month_days),
        "per_question": dollars(day_cost / questions, "0.0001"),
        "test_questions": "500",
    }
