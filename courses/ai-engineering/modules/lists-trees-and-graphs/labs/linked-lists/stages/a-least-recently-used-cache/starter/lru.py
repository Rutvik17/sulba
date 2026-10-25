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
        raise NotImplementedError

    def get(self, key):
        """The key's value, or -1 if the cache doesn't hold it."""
        raise NotImplementedError

    def put(self, key, value):
        """Sets the key's value, dropping the least recently used key if the key is new and
        the cache is full."""
        raise NotImplementedError
