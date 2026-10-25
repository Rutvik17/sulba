class Node:
    """A node of a singly linked list: its value, and the next node or None."""

    def __init__(self, value, next=None):
        self.value = value
        self.next = next


def cycle_start(head):
    """The first node of the cycle the list runs into, or None if it ends."""
    raise NotImplementedError
