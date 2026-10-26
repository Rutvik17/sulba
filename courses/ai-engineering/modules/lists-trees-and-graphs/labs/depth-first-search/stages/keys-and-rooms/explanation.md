```python
def all_opened(rooms):
    opened = {0}
    stack = [0]
    while stack:
        for key in rooms[stack.pop()]:
            if key not in opened:
                opened.add(key)
                stack.append(key)
    return len(opened) == len(rooms)
```

The rooms and keys are a graph: a key in room `i` is an edge from `i` to the room it opens. A search from room 0 reaches every room it can, and `opened` keeps it from entering one twice, so each room and each key is looked at once. Taking rooms off the end of the list makes the search depth first, with no calls: the tests' rooms in a chain, each holding the next one's key, go {% $fig.rooms %} deep, far past Python's recursion limit for a search that calls itself.
