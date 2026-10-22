import gc
import random

import pytest
from add import Node, add

DIGITS = 200_000

# Every node a test makes or walks, kept until the test ends.
kept = []


@pytest.fixture(autouse=True)
def unlinked():
    """Unlinks every node when a test ends, so that a long list is freed a node at a time."""
    yield
    for each in gc.get_objects():
        if type(each) is Node:
            each.next = None
    kept.clear()


def build(values):
    """A list of new nodes holding the values, and its head."""
    head = None
    for value in reversed(values):
        head = Node(value, head)
        kept.append(head)
    return head


def values(head, most=10**7):
    """The values from head on, stopping after most of them."""
    found = []
    while head is not None and len(found) < most:
        kept.append(head)
        found.append(head.value)
        head = head.next
    return found


def digits_of(value):
    """value's digits, the ones digit first."""
    found = []
    while True:
        value, digit = divmod(value, 10)
        found.append(digit)
        if value == 0:
            return found


@pytest.mark.id("tst_uu4nz2")
def test_add():
    """Adds two digit lists"""
    assert values(add(build([2, 4, 3]), build([5, 6, 4]))) == [7, 0, 8]


@pytest.mark.id("tst_d2f87j")
def test_edges():
    """Carries into a new digit, adds lists of different lengths and adds 0"""
    assert values(add(build([9, 9]), build([1]))) == [0, 0, 1]
    assert values(add(build([0]), build([0]))) == [0]
    assert values(add(build([1]), build([9, 9, 9, 9]))) == [0, 0, 0, 0, 1]
    a = build([5, 5])
    b = build([5])
    add(a, b)
    assert values(a) == [5, 5] and values(b) == [5]


@pytest.mark.id("tst_k7j2x4")
def test_numbers():
    """Matches adding the numbers"""
    rng = random.Random(84)
    for _ in range(300):
        x, y = rng.randint(0, 10**12), rng.randint(0, 10**6)
        assert values(add(build(digits_of(x)), build(digits_of(y)))) == digits_of(x + y)


@pytest.mark.id("tst_26b0u4")
def test_long():
    """Adds numbers with many digits in time"""
    rng = random.Random(85)
    a = [rng.randint(0, 9) for _ in range(DIGITS - 1)] + [rng.randint(1, 9)]
    b = [9 - digit for digit in a[:-1]] + [9]
    # a + b: every place but the last adds to 9, and the last to 9 or more.
    total = values(add(build(a), build(b)), most=DIGITS + 2)
    carry, expected = 0, []
    for x, y in zip(a, b):
        carry, digit = divmod(x + y + carry, 10)
        expected.append(digit)
    if carry:
        expected.append(carry)
    assert total == expected
