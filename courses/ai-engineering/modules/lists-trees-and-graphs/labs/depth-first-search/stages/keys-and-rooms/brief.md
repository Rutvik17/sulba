Room 0 is open and every other room is locked. `rooms[i]` is the list of keys in room `i`, each key the number of the room it opens. Write `all_opened`:

```
all_opened(rooms) -> whether every room can be entered, starting from room 0
```

`all_opened([[1], [2], [3], []])` returns `True`, and `all_opened([[1, 3], [3, 0, 1], [2], [0]])` returns `False`: the only key to room 2 is in room 2. The tests' longest list has {% $fig.rooms %} rooms.
