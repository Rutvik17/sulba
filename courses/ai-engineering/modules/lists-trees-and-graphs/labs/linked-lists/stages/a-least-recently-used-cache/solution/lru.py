class Node:
    """A key and its value, linked to the nodes used just before and just after it."""

    def __init__(self, key, value):
        self.key = key
        self.value = value
        self.before = None
        self.after = None


class Cache:
    """At most capacity keys, dropping the least recently used when a new key comes."""

    def __init__(self, capacity):
        self.capacity = capacity
        self.nodes = {}
        # One node at both ends of a circle: the oldest is after it, the newest before it.
        self.ends = Node(None, None)
        self.ends.before = self.ends.after = self.ends

    def get(self, key):
        """The key's value, or -1 if the cache doesn't hold it."""
        node = self.nodes.get(key)
        if node is None:
            return -1
        self.unlink(node)
        self.add_newest(node)
        return node.value

    def put(self, key, value):
        """Sets the key's value, dropping the least recently used key if the key is new and
        the cache is full."""
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
