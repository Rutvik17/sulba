```python
def reorder(head):
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
```

The fast pointer moves two nodes for the slow one's one, so when it reaches the end, the slow one is at the middle: the end of the first half, which keeps the extra node of an odd list. The second half is cut off there and reversed, so its nodes come last first. Then the two halves interleave, a node of the front, a node of the back. Each step walks the list once: time in proportion to its length, and a few names of space.

Walking from each front node to the last node of what's left, to take it from the end, works too, but it walks most of what's left each time: {% $fig.walks %} steps for the longest test's {% $fig.nodes %} nodes. A list of the nodes reaches the last one at once, and holds every node, which the brief rules out: the longest test measures the memory the call allocates with `tracemalloc` and allows {% $fig.allowed %}.
