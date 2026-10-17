import json
import math
from pathlib import Path

import pytest

from engine import Value, exp, topological_order

CASES = json.loads(Path("references/scalars.json").read_text())["first_operations"]
# PyTorch's results and yours may differ in the last digits, from working in another order.
RTOL, ATOL = 1e-10, 1e-12


def evaluate(steps):
    """The last step's Value and the inputs' Values, from an expression written as steps,
    each an operation on the results of steps before it."""
    values, inputs = [], []
    for op, *args in steps:
        if op == "input":
            value = Value(args[0])
            inputs.append(value)
        elif op == "add":
            value = values[args[0]] + values[args[1]]
        elif op == "mul":
            value = values[args[0]] * values[args[1]]
        elif op == "add_number":
            value = values[args[0]] + args[1]
        elif op == "number_mul":
            value = args[1] * values[args[0]]
        elif op == "exp":
            value = exp(values[args[0]])
        values.append(value)
    return values[-1], inputs


@pytest.mark.id("tst_1xgnq9")
def test_by_hand():
    """A sum of a product, its value and gradients worked by hand"""
    a, b = Value(2.0), Value(-3.0)
    c = a * b + a
    c.backward()
    assert c.data == -4.0
    assert a.grad == -2.0 and b.grad == 2.0


@pytest.mark.id("tst_zdliz0")
def test_numbers_on_either_side():
    """A number on either side of + and *"""
    a = Value(1.5)
    out = 2 + 3 * a + 1 * a * 2
    out.backward()
    assert isinstance(out, Value)
    assert out.data == pytest.approx(9.5)
    assert a.grad == pytest.approx(5.0)


@pytest.mark.id("tst_chz3o5")
def test_used_twice():
    """A value used twice gets a gradient from each use"""
    a = Value(3.0)
    (a * a).backward()
    assert a.grad == pytest.approx(6.0)
    b = Value(-1.0)
    (b + b + b).backward()
    assert b.grad == pytest.approx(3.0)


@pytest.mark.id("tst_rtcwwv")
def test_exp():
    """exp's value and derivative"""
    a = Value(1.5)
    out = exp(a)
    out.backward()
    assert out.data == pytest.approx(math.exp(1.5), rel=1e-15)
    assert a.grad == pytest.approx(math.exp(1.5), rel=1e-15)


@pytest.mark.id("tst_0tdkqk")
def test_matches_pytorch():
    """The same value and gradients as PyTorch's, for each recorded expression"""
    for case in CASES:
        out, inputs = evaluate(case["steps"])
        out.backward()
        assert out.data == pytest.approx(case["value"], rel=RTOL, abs=ATOL)
        found = [value.grad for value in inputs]
        assert found == pytest.approx(case["gradients"], rel=RTOL, abs=ATOL)


@pytest.mark.id("tst_qg4b0x")
def test_order():
    """Every value once, each after the values it was made from"""
    for case in CASES:
        out, _ = evaluate(case["steps"])
        order = topological_order(out)
        assert order[-1] is out
        assert len({id(value) for value in order}) == len(order)
        seen = set()
        for value in order:
            assert all(id(parent) in seen for parent in value._parents)
            seen.add(id(value))


@pytest.mark.id("tst_aypyot")
def test_unused_input():
    """A value the output wasn't made from keeps a gradient of 0"""
    a, unused = Value(2.0), Value(5.0)
    (a * 4).backward()
    assert a.grad == 4.0 and unused.grad == 0.0
