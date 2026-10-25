class Node:
    """A node of a singly linked list: its value, and the next node or None."""

    def __init__(self, value, next=None):
        self.value = value
        self.next = next


def remove_from_end(head, n):
    """The list from head without its nth node from the end, 1 being the last."""
    before = Node(None, head)
    ahead = behind = before
    for _ in range(n):
        ahead = ahead.next
    while ahead.next is not None:
        ahead = ahead.next
        behind = behind.next
    behind.next = behind.next.next
    return before.next
