import random

import pytest

from expressions import evaluate

GROUPS = 50_000
DEPTH = 300


def built(rng, depth):
    """A random expression and its value, at most depth parentheses deep."""
    if not depth or rng.random() < 0.3:
        number = rng.randint(-20, 20)
        return str(number), number
    operator = rng.choice("+-*")
    operands = [built(rng, depth - 1) for _ in range(rng.randint(1, 4))]
    values = [value for _, value in operands]
    if operator == "+":
        value = sum(values)
    elif operator == "*":
        value = 1
        for each in values:
            value *= each
    else:
        value = -values[0] if len(values) == 1 else values[0] - sum(values[1:])
    space = " " * rng.randint(1, 2)
    text = "(" + operator + space + space.join(text for text, _ in operands) + ")"
    return text, value


@pytest.mark.id("tst_j2006w")
def test_evaluate():
    """Evaluates nested prefix expressions"""
    assert evaluate("(+ 1 (* 2 3) 4)") == 11
    assert evaluate("(- (* 2 5) 3 (- 1))") == 8
    assert evaluate("(*(+ 1 2)(- 4 1))") == 9


@pytest.mark.id("tst_jvv9t3")
def test_edges():
    """Handles a bare number, one operand, and extra spaces"""
    assert evaluate("42") == 42
    assert evaluate("-7") == -7
    assert evaluate("(+ 5)") == 5
    assert evaluate("(* 3)") == 3
    assert evaluate("(- 5)") == -5
    assert evaluate("(- 10 3 2)") == 5
    assert evaluate("  ( +   1    2 )  ") == 3


@pytest.mark.id("tst_up3u7r")
def test_random():
    """Matches the values of random expressions"""
    rng = random.Random(331)
    for _ in range(300):
        text, value = built(rng, 5)
        assert evaluate(text) == value


@pytest.mark.id("tst_i916t4")
def test_long():
    """Evaluates a long expression and a deep one in time"""
    longest = "(+ " + " ".join(f"(* {n} {n + 1})" for n in range(GROUPS)) + ")"
    assert evaluate(longest) == sum(n * (n + 1) for n in range(GROUPS))
    deepest = "1"
    for _ in range(DEPTH):
        deepest = f"(* 2 {deepest})"
    assert evaluate(deepest) == 2**DEPTH
