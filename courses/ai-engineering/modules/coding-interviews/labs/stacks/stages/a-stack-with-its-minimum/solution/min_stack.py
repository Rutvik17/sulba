class MinStack:
    """A stack that also knows its smallest value, each method in constant time."""

    def __init__(self):
        self._items = []

    def push(self, value):
        least = min(value, self._items[-1][1]) if self._items else value
        self._items.append((value, least))

    def pop(self):
        return self._items.pop()[0]

    def top(self):
        return self._items[-1][0]

    def minimum(self):
        return self._items[-1][1]
