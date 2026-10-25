```python
def reverse(head):
    reversed_head = None
    while head is not None:
        following = head.next
        head.next = reversed_head
        reversed_head = head
        head = following
    return reversed_head
```

`reversed_head` is the front of the part already reversed. Each node is taken off the front of what's left and put on the front of that part, so the last node taken is the new head. `following` keeps the rest of the list reachable once `head.next` changes. Each node is visited once: time in proportion to the list, and three names of extra space.

A recursive reversal, which reverses the rest of the list and then puts the head at its end, makes a call for each node: {% $fig.nodes %} calls deep for the longest test. Python's recursion limit, the deepest its calls may go, is {% $fig.limit %}, so it raises `RecursionError` long before. The loop does the same work with no depth at all.
