class Node:
    """A node of a singly linked list: its value, and the next node or None."""

    def __init__(self, value, next=None):
        self.value = value
        self.next = next


def reorder(head):
    """head, its list relinked as the first node, the last, the second, the one before the
    last, and so on."""
    if head is None:
        return None
    slow = fast = head
    while fast.next is not None and fast.next.next is not None:
        slow = slow.next
        fast = fast.next.next
    second, slow.next = slow.next, None
    back = None
    while second is not None:
        second.next, back, second = back, second, second.next
    front = head
    while back is not None:
        front.next, front = back, front.next
        back.next, back = front, back.next
    return head
