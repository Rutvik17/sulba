from decimal import Decimal

import pytest

from costs import PRICES, Tokens, anthropic_tokens, cost, month, openai_tokens

LUNA, SOL = PRICES["gpt-6-luna"], PRICES["gpt-6.1-sol"]
HAIKU, SONNET = PRICES["claude-haiku-5-5"], PRICES["claude-sonnet-5-5"]


@pytest.mark.id("tst_rv9fpi")
def test_openai_usage():
    """OpenAI's prompt tokens, less those read from the cache and written to it"""
    cached = {
        "prompt_tokens": 2048,
        "completion_tokens": 120,
        "total_tokens": 2168,
        "prompt_tokens_details": {"cached_tokens": 1792, "cache_write_tokens": 0},
    }
    assert openai_tokens(cached) == Tokens(256, 1792, 0, 120)
    written = {
        "prompt_tokens": 1850,
        "completion_tokens": 90,
        "prompt_tokens_details": {"cached_tokens": 0, "cache_write_tokens": 1800},
    }
    assert openai_tokens(written) == Tokens(50, 0, 1800, 90)
    assert openai_tokens({"prompt_tokens": 19, "completion_tokens": 9}) == Tokens(
        19, 0, 0, 9
    )
    unknown = {
        "prompt_tokens": 30,
        "completion_tokens": 5,
        "prompt_tokens_details": None,
    }
    assert openai_tokens(unknown) == Tokens(30, 0, 0, 5)
    empty = {"prompt_tokens": 30, "completion_tokens": 5, "prompt_tokens_details": {}}
    assert openai_tokens(empty) == Tokens(30, 0, 0, 5)


@pytest.mark.id("tst_glsvpg")
def test_anthropic_usage():
    """Anthropic's input tokens, beside those read from the cache and written to it"""
    written = {
        "input_tokens": 50,
        "cache_creation_input_tokens": 1800,
        "cache_read_input_tokens": 0,
        "output_tokens": 90,
    }
    assert anthropic_tokens(written) == Tokens(50, 0, 1800, 90)
    cached = {
        "input_tokens": 250,
        "cache_creation_input_tokens": None,
        "cache_read_input_tokens": 1800,
        "output_tokens": 90,
    }
    assert anthropic_tokens(cached) == Tokens(250, 1800, 0, 90)
    assert anthropic_tokens({"input_tokens": 19, "output_tokens": 9}) == Tokens(
        19, 0, 0, 9
    )


@pytest.mark.id("tst_3i1vzn")
def test_cost():
    """Each kind of token at its own price, in dollars, exactly"""
    found = cost(Tokens(256, 1792, 0, 120), LUNA)
    assert isinstance(found, Decimal) and found == Decimal("0.00010352")
    assert cost(Tokens(50, 0, 1800, 90), SONNET) == Decimal("0.0055")
    assert cost(Tokens(250, 1800, 0, 90), HAIKU) == Decimal("0.000088")
    assert cost(Tokens(1000, 0, 0, 500), SOL) == Decimal("0.007")
    assert cost(Tokens(0, 0, 0, 0), LUNA) == 0


@pytest.mark.id("tst_o2cwkb")
def test_long_prompts():
    """A prompt over a model's limit pays its long prices for every token"""
    assert cost(Tokens(272_000, 0, 0, 1000), LUNA) == Decimal("0.0277")
    assert cost(Tokens(272_001, 0, 0, 1000), LUNA) == Decimal("0.0551502")
    assert cost(Tokens(1, 272_000, 0, 1000), LUNA) == Decimal("0.0061902")
    assert cost(Tokens(500, 99_500, 0, 100), HAIKU) == Decimal("0.001095")
    assert cost(Tokens(500, 99_501, 0, 100), HAIKU) == Decimal("0.00547505")
    assert cost(Tokens(0, 0, 100_001, 100), HAIKU) == Decimal("0.062750625")
    assert cost(Tokens(900_000, 0, 0, 1000), SONNET) == Decimal("1.81")


@pytest.mark.id("tst_l3sh6l")
def test_month():
    """A month of requests, each priced on its own"""
    requests = [Tokens(272_001, 0, 0, 1000), Tokens(1000, 0, 0, 100)]
    assert month(requests, LUNA) == Decimal("0.0553002")
    assert month([Tokens(1000, 0, 0, 500)] * 3, SOL) == Decimal("0.021")
    assert month([], HAIKU) == 0
