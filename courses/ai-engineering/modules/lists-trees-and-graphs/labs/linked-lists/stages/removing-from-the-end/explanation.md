```python
def remove_from_end(head, n):
    before = Node(None, head)
    ahead = behind = before
    for _ in range(n):
        ahead = ahead.next
    while ahead.next is not None:
        ahead = ahead.next
        behind = behind.next
    behind.next = behind.next.next
    return before.next
```

`before` is a node in front of the head, so that every node, the head included, has a node before it. `ahead` starts `n` nodes past `behind`, and they move together until `ahead` is the last node. `behind` is then `n` nodes before the last: the node just before the one to remove, which it skips. The list is walked once, in time in proportion to its length, with three names of space.

Counting the list first and then walking to the node before the one to remove reads the list twice, in the same proportion. The node in front is what saves the special case: without it, removing the head needs a branch of its own.
