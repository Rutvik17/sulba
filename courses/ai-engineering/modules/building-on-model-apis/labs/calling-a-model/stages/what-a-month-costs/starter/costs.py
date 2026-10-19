"""What the shop's assistant's requests cost, from each provider's report of their tokens and its
published prices."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

MILLION = 1_000_000


@dataclass(frozen=True)
class Tokens:
    """A request's tokens, by how they're priced: the prompt's tokens read fresh, read from the
    provider's cache and written to it, and the reply's tokens."""

    fresh: int
    cached: int
    written: int
    output: int


@dataclass(frozen=True)
class Price:
    """A model's prices in dollars per million tokens of each kind. A request whose prompt has
    more than `above` tokens pays the prices of `long` for all its tokens."""

    fresh: Decimal
    cached: Decimal
    written: Decimal
    output: Decimal
    above: int | None = None
    long: "Price | None" = None


# Each provider's published prices on 19 October 2026 for its standard service, in dollars per
# million tokens: fresh, cached and written prompt tokens, and output. Anthropic's cache writes
# are the five-minute kind.
PRICES = {
    "gpt-6-luna": Price(
        Decimal("0.10"),
        Decimal("0.01"),
        Decimal("0.125"),
        Decimal("0.50"),
        above=272_000,
        long=Price(Decimal("0.20"), Decimal("0.02"), Decimal("0.25"), Decimal("0.75")),
    ),
    "gpt-6.1-sol": Price(
        Decimal("2"),
        Decimal("0.10"),
        Decimal("2.50"),
        Decimal("10"),
        above=272_000,
        long=Price(Decimal("4"), Decimal("0.20"), Decimal("5"), Decimal("15")),
    ),
    "claude-haiku-5-5": Price(
        Decimal("0.10"),
        Decimal("0.01"),
        Decimal("0.125"),
        Decimal("0.50"),
        above=100_000,
        long=Price(Decimal("0.50"), Decimal("0.05"), Decimal("0.625"), Decimal("2.50")),
    ),
    "claude-sonnet-5-5": Price(
        Decimal("2"), Decimal("0.10"), Decimal("2.50"), Decimal("10")
    ),
}


def openai_tokens(usage: dict[str, Any]) -> Tokens:
    """The tokens of a chat completion's usage from OpenAI's API, whose prompt_tokens include
    those read from the cache and written to it."""
    raise NotImplementedError


def anthropic_tokens(usage: dict[str, Any]) -> Tokens:
    """The tokens of a message's usage from Anthropic's API, whose input_tokens leave out those
    read from the cache and written to it."""
    raise NotImplementedError


def cost(tokens: Tokens, price: Price) -> Decimal:
    """What the request costs in dollars, exactly."""
    raise NotImplementedError


def month(requests: list[Tokens], price: Price) -> Decimal:
    """What the requests cost in dollars, each priced on its own."""
    raise NotImplementedError
