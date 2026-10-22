class Node:
    """A node of a singly linked list: its value, and the next node or None."""

    def __init__(self, value, next=None):
        self.value = value
        self.next = next


def reverse(head):
    """The list from head, reversed: its own nodes, relinked."""
    reversed_head = None
    while head is not None:
        following = head.next
        head.next = reversed_head
        reversed_head = head
        head = following
    return reversed_head
