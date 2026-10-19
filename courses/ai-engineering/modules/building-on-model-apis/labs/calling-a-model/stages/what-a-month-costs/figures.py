from decimal import ROUND_HALF_UP, Decimal

MILLION = 1_000_000
PRICED = "19 October 2026"
# Each model's standard prices that day, in dollars per million tokens: fresh, cached and
# written prompt tokens, and output. None of the shop's prompts reaches a long-prompt price.
PRICES = {
    "gpt-6-luna": (Decimal("0.10"), Decimal("0.01"), Decimal("0.125"), Decimal("0.50")),
    "gpt-6.1-sol": (Decimal("2"), Decimal("0.10"), Decimal("2.50"), Decimal("10")),
    "claude-haiku-5-5": (
        Decimal("0.10"),
        Decimal("0.01"),
        Decimal("0.125"),
        Decimal("0.50"),
    ),
    "claude-sonnet-5-5": (
        Decimal("2"),
        Decimal("0.10"),
        Decimal("2.50"),
        Decimal("10"),
    ),
}
# The shop's month: its conversations, the questions in each, the tokens of its instructions,
# what each question adds to the prompt with the replies before it, and each reply.
CONVERSATIONS, QUESTIONS = 2000, 3
INSTRUCTIONS, FIRST, LATER, REPLY = 1800, 50, 250, 90


def month(first, later, price):
    """The month's cost when each conversation's first request has the tokens first, and each
    later one the tokens later: fresh, cached, written and output."""

    def cost(tokens):
        return sum(n * p for n, p in zip(tokens, price, strict=True)) / MILLION

    return CONVERSATIONS * cost(first) + CONVERSATIONS * (QUESTIONS - 1) * cost(later)


def dollars(amount):
    return f"${amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):,}"


def figures():
    # Read fresh, every request pays for the instructions in full.
    fresh = {
        model: month(
            (INSTRUCTIONS + FIRST, 0, 0, REPLY),
            (INSTRUCTIONS + LATER, 0, 0, REPLY),
            price,
        )
        for model, price in PRICES.items()
    }
    luna = PRICES["gpt-6-luna"]
    # Each conversation's first request writes the instructions to the cache, and the later
    # ones read them from it.
    cached = month(
        (FIRST, 0, INSTRUCTIONS, REPLY), (LATER, INSTRUCTIONS, 0, REPLY), luna
    )
    # OpenAI's prompt_tokens read as fresh tokens, with the cached and written ones on top.
    misread = month(
        (FIRST + INSTRUCTIONS, 0, INSTRUCTIONS, REPLY),
        (LATER + INSTRUCTIONS, INSTRUCTIONS, 0, REPLY),
        luna,
    )
    assert fresh["gpt-6-luna"] == fresh["claude-haiku-5-5"]
    assert fresh["gpt-6.1-sol"] == fresh["claude-sonnet-5-5"]
    times = fresh["gpt-6.1-sol"] / fresh["gpt-6-luna"]
    assert times == int(times)
    return {
        "priced": PRICED,
        "conversations": f"{CONVERSATIONS:,}",
        "questions": str(QUESTIONS),
        "instructions": f"{INSTRUCTIONS:,}",
        "first": str(FIRST),
        "later": str(LATER),
        "reply": str(REPLY),
        "small_month": dollars(fresh["gpt-6-luna"]),
        "large_month": dollars(fresh["gpt-6.1-sol"]),
        "times": str(int(times)),
        "cached_month": dollars(cached),
        "misread_month": dollars(misread),
    }
