```python
def cycle_start(head):
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
```

The fast pointer moves two nodes for the slow one's one. A list that ends lets the fast one reach `None`. In a cycle, the fast one gains a node on the slow one at each step once both are in it, so it catches it within one lap.

Say the cycle starts `a` nodes from the head, and they meet `b` nodes into it, in a cycle of `c` nodes. The slow pointer has walked `a + b`, and the fast one twice that, which is also `a + b` plus some whole laps: `a + b` is a multiple of `c`. So from the meeting point, `a` more steps reach the cycle's start, which is also `a` steps from the head. Two pointers, one from the head and one from the meeting point, meet there. It takes time in proportion to the list, and two names of space.

A set of the nodes seen finds the start as the first node seen twice, in the same time, but it holds every node it passes, {% $fig.nodes %} of them for the longest test. The test measures the memory the call allocates with `tracemalloc` and allows {% $fig.allowed %}.
