class Node:
    """A node of a singly linked list: its value, and the next node or None."""

    def __init__(self, value, next=None):
        self.value = value
        self.next = next


def add(a, b):
    """The digits of the sum of the numbers whose digits a and b hold, the ones digit first."""
    before = tail = Node(None)
    carry = 0
    while a is not None or b is not None or carry:
        total = carry
        if a is not None:
            total += a.value
            a = a.next
        if b is not None:
            total += b.value
            b = b.next
        carry, digit = divmod(total, 10)
        tail.next = Node(digit)
        tail = tail.next
    return before.next
