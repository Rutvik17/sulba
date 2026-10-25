"""The summary the office reads: every number computed from the trials and the office's
figures, and each interval's ends rounded outward."""

from mix import OFFICE
from worth import AGENT, HOST, MINUTES, PRICE, SUPPORT

NAMES = {
    "question": "Questions",
    "case": "Cases",
    "callback": "Callbacks",
    "new": "New tickets",
    "vague": "Vague requests",
}


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
    raise NotImplementedError
