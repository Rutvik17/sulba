class Node:
    """A node of a linked list: its value, the next node or None, and random, any node of the
    list or None."""

    def __init__(self, value, next=None, random=None):
        self.value = value
        self.next = next
        self.random = random


def copy_list(head):
    """A copy of the list from head, with new nodes, linked as the original's are."""
    raise NotImplementedError
