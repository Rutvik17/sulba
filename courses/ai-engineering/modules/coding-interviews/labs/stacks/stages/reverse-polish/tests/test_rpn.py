import random

import pytest
from rpn import evaluate

NUMBERS = 50_001


def tree(rng, depth):
    """A random expression: a number, or (left, operator, right)."""
    if depth == 0 or rng.random() < 0.3:
        return rng.randint(-9, 9)
    return (
        tree(rng, depth - 1),
        rng.choice(["+", "-", "*", "//"]),
        tree(rng, depth - 1),
    )


def value(expression):
    """The value of an expression tree, or None if it divides by zero."""
    if isinstance(expression, int):
        return expression
    left, operator, right = expression
    a, b = value(left), value(right)
    if a is None or b is None or (operator == "//" and b == 0):
        return None
    return {"+": a + b, "-": a - b, "*": a * b, "//": a // b if b else None}[operator]


def tokens_of(expression):
    """The expression tree written in reverse Polish notation."""
    if isinstance(expression, int):
        return [str(expression)]
    left, operator, right = expression
    return tokens_of(left) + tokens_of(right) + [operator]


@pytest.mark.id("tst_omgmuz")
def test_evaluate():
    """Evaluates reverse Polish notation"""
    assert evaluate(["7", "2", "-", "3", "*"]) == 15
    assert evaluate(["4", "13", "5", "//", "+"]) == 6


@pytest.mark.id("tst_2mji73")
def test_order():
    """Keeps operands in order, divides as Python does, and reads negative numbers"""
    assert evaluate(["10", "3", "-"]) == 7
    assert evaluate(["-7", "2", "//"]) == -4
    assert evaluate(["-3", "-4", "*"]) == 12
    assert evaluate(["42"]) == 42


@pytest.mark.id("tst_tdjrs1")
def test_trees():
    """Matches evaluating the expression as a tree"""
    rng = random.Random(43)
    checked = 0
    while checked < 300:
        expression = tree(rng, 4)
        expected = value(expression)
        if expected is None:
            continue
        assert evaluate(tokens_of(expression)) == expected
        checked += 1


@pytest.mark.id("tst_14o9u2")
def test_long():
    """Evaluates a long expression in time"""
    tokens = ["1"] * NUMBERS + ["+"] * (NUMBERS - 1)
    assert evaluate(tokens) == NUMBERS
