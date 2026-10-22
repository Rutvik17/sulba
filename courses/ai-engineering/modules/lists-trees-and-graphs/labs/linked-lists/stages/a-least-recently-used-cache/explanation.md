```python
class Cache:
    def __init__(self, capacity):
        self.capacity = capacity
        self.nodes = {}
        self.ends = Node(None, None)
        self.ends.before = self.ends.after = self.ends

    def get(self, key):
        node = self.nodes.get(key)
        if node is None:
            return -1
        self.unlink(node)
        self.add_newest(node)
        return node.value

    def put(self, key, value):
        node = self.nodes.get(key)
        if node is not None:
            node.value = value
            self.unlink(node)
        else:
            if len(self.nodes) == self.capacity:
                oldest = self.ends.after
                self.unlink(oldest)
                del self.nodes[oldest.key]
            node = Node(key, value)
            self.nodes[key] = node
        self.add_newest(node)

    def unlink(self, node):
        node.before.after = node.after
        node.after.before = node.before

    def add_newest(self, node):
        node.before, node.after = self.ends.before, self.ends
        self.ends.before.after = node
        self.ends.before = node
```

The dict finds a key's node, and the list keeps the nodes in the order they were used, oldest just after `ends` and newest just before it. One node, `ends`, stands at both ends of a circle, so every node has a neighbour on each side and no step needs a branch for an empty list. Using a key unlinks its node and links it in again as the newest, and a full cache drops the node after `ends`. Every step is a few links and a dict lookup: constant time for each `get` and `put`, and space for the capacity.

Keeping the keys in a Python list in the order used, and moving a key with `list.remove` and `append`, is correct but `remove` searches the list. For the longest test's {% $fig.operations %} operations on a cache of {% $fig.capacity %}, that's up to {% $fig.searches %} steps. Python's `collections.OrderedDict` does the same job: `move_to_end(key)` and `popitem(last=False)` are the two steps above.
