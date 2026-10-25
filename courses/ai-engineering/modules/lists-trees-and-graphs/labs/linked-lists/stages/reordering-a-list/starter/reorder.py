class Node:
    """A node of a singly linked list: its value, and the next node or None."""

    def __init__(self, value, next=None):
        self.value = value
        self.next = next


def reorder(head):
    """head, its list relinked as the first node, the last, the second, the one before the
    last, and so on."""
    raise NotImplementedError
