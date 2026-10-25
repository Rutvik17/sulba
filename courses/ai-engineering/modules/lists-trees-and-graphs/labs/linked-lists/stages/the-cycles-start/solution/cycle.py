class Node:
    """A node of a singly linked list: its value, and the next node or None."""

    def __init__(self, value, next=None):
        self.value = value
        self.next = next


def cycle_start(head):
    """The first node of the cycle the list runs into, or None if it ends."""
    slow = fast = head
    while fast is not None and fast.next is not None:
        slow = slow.next
        fast = fast.next.next
        if slow is fast:
            slow = head
            while slow is not fast:
                slow = slow.next
                fast = fast.next
            return slow
    return None
