"""The summary the office reads: every number computed from the trials and the office's
figures, and each interval's ends rounded outward."""

import math
from statistics import NormalDist

from kinds import by_kind
from mix import OFFICE, weighted
from worth import AGENT, HOST, MINUTES, PRICE, SUPPORT, monthly, payback, seconds

NAMES = {
    "question": "Questions",
    "case": "Cases",
    "callback": "Callbacks",
    "new": "New tickets",
    "vague": "Vague requests",
}


def percent(share: float, rounding=round) -> str:
    """A share in percent to a tenth, rounded as given."""
    return f"{rounding(share * 1000) / 10:.1f}%"


def dollars(amount: float, rounding=round) -> str:
    """Dollars to the whole dollar, rounded as given, with a minus sign before a loss."""
    whole = rounding(amount)
    return f"-${-whole:,}" if whole < 0 else f"${whole:,}"


def months(count: float, rounding=round) -> str:
    """Months to a tenth, rounded as given."""
    return f"{rounding(count * 10) / 10:.1f}"


def summary(
    runs: list[dict[str, str]],
    variant: str,
    volumes: dict[str, int] = OFFICE,
    minutes: dict[str, float] = MINUTES,
    agent: float = AGENT,
    host: float = HOST,
    support: float = SUPPORT,
    price: float = PRICE,
    confidence: float = 0.95,
) -> str:
    """The summary's lines, for the variant's runs, from runs.csv's rows."""
    shares = by_kind(runs, variant)
    share = weighted(shares, volumes, confidence)
    z = NormalDist().inv_cdf((1 + confidence) / 2)
    lines = [
        f"The desk does {percent(share.value)} of the office's {sum(volumes.values()):,}"
        f" contacts a month, from {percent(share.low, math.floor)}"
        f" to {percent(share.high, math.ceil)}."
    ]
    for kind, count in volumes.items():
        if count == 0:
            continue
        each = shares[kind]
        if each.error == 0 and each.value == 1:
            lines.append(f"{NAMES[kind]}: all {each.tasks} tasks done in every trial.")
        elif each.error == 0 and each.value == 0:
            lines.append(
                f"{NAMES[kind]}: none of {each.tasks} tasks done in any trial."
            )
        else:
            low = max(each.value - z * each.error, 0.0)
            high = min(each.value + z * each.error, 1.0)
            lines.append(
                f"{NAMES[kind]}: {percent(each.value)} of {each.tasks} tasks,"
                f" from {percent(low, math.floor)} to {percent(high, math.ceil)}."
            )
    net = monthly(
        shares,
        seconds(runs, variant),
        volumes,
        minutes,
        agent,
        host,
        support,
        confidence,
    )
    lines.append(
        f"It saves {dollars(net.value)} a month net, from {dollars(net.low, math.floor)}"
        f" to {dollars(net.high, math.ceil)}."
    )
    back = payback(price, net)
    if math.isinf(back.value):
        lines.append("At these figures the pilot doesn't pay for itself.")
    elif math.isinf(back.high):
        lines.append(
            f"The pilot pays for itself in {months(back.value)} months, from"
            f" {months(back.low, math.floor)}, or not at all at the saving's low end."
        )
    else:
        lines.append(
            f"The pilot pays for itself in {months(back.value)} months, from"
            f" {months(back.low, math.floor)} to {months(back.high, math.ceil)}."
        )
    return "\n".join(lines)
