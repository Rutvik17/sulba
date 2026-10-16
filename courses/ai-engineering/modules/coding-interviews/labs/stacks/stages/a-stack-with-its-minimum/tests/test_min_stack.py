import random

import pytest
from min_stack import MinStack

VALUES = 100_000


@pytest.mark.id("tst_i6h762")
def test_stack():
    """Pushes, pops and gives the top and the minimum"""
    stack = MinStack()
    stack.push(5)
    stack.push(2)
    stack.push(7)
    assert stack.minimum() == 2
    assert stack.top() == 7
    assert stack.pop() == 7
    assert stack.pop() == 2
    assert stack.minimum() == 5


@pytest.mark.id("tst_qv4kvm")
def test_repeats():
    """Keeps a minimum pushed twice until both are popped"""
    stack = MinStack()
    for value in [3, 1, 4, 1]:
        stack.push(value)
    stack.pop()
    assert stack.minimum() == 1
    stack.pop()
    stack.pop()
    assert stack.minimum() == 3


@pytest.mark.id("tst_0dmtb0")
def test_empty():
    """Raises IndexError when empty"""
    stack = MinStack()
    for method in (stack.pop, stack.top, stack.minimum):
        with pytest.raises(IndexError):
            method()
    stack.push(1)
    stack.pop()
    with pytest.raises(IndexError):
        stack.minimum()


@pytest.mark.id("tst_pl5bw4")
def test_list():
    """Matches a list and min, over random pushes and pops"""
    rng = random.Random(45)
    for _ in range(100):
        stack, values = MinStack(), []
        for _ in range(30):
            if values and rng.random() < 0.4:
                assert stack.pop() == values.pop()
            else:
                value = rng.randint(-9, 9)
                stack.push(value)
                values.append(value)
            if values:
                assert stack.top() == values[-1]
                assert stack.minimum() == min(values)


@pytest.mark.id("tst_yofyg6")
def test_long():
    """Gives the minimum of a tall stack in time"""
    stack = MinStack()
    for value in range(VALUES):
        stack.push(VALUES - value if value % 2 else value)
        assert stack.minimum() == 0
