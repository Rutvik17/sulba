```python
class MinStack:
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
```

Each item keeps the minimum of the stack from the bottom up to it, so the top item's minimum is the stack's, and popping it uncovers the minimum the stack had before. Every method touches only the top, so each takes constant time, and the stack holds twice as many values. On an empty list, `pop()` and `[-1]` raise `IndexError` by themselves.

Finding the minimum with `min` over the stack reads every value each time: for the longest test, {% $fig.reads %} reads, far past the time limit.
