```python
def copy_list(head):
    copies = {None: None}
    node = head
    while node is not None:
        copies[node] = Node(node.value)
        node = node.next
    node = head
    while node is not None:
        copies[node].next = copies[node.next]
        copies[node].random = copies[node.random]
        node = node.next
    return copies[head]
```

The first walk makes every copy, so the second can link each one to the copies of its original's `next` and `random`, whichever comes first in the list. The dict's key for `None` maps to `None`, so the list's end and a missing `random` need no branch. A node is hashed by its identity, which is what the dict needs: two nodes with the same value are still two nodes. Two walks and a dict: time and space in proportion to the list.

Finding a `random` node's place by walking from the head, then walking the copy to the same place, takes two walks for each node: {% $fig.walks %} steps for the longest test's {% $fig.nodes %} nodes, whose `random` links all point into the list's second half.

A copy can be made without the dict, by putting each copy just after its original, setting the copies' `random` links from their originals', then splitting the two lists. It uses no extra space beyond the copy, and changes the original while it runs.
