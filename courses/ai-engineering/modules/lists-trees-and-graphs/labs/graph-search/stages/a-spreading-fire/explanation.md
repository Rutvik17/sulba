```python
def minutes_to_burn(rows):
    burning = [
        (y, x)
        for y, row in enumerate(rows)
        for x, square in enumerate(row)
        if square == "F"
    ]
    trees = sum(row.count("T") for row in rows)
    caught = set(burning)
    minutes = 0
    while burning and trees:
        spreading = []
        for y, x in burning:
            for near in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
                ny, nx = near
                tree = (
                    0 <= ny < len(rows)
                    and 0 <= nx < len(rows[ny])
                    and rows[ny][nx] == "T"
                )
                if tree and near not in caught:
                    caught.add(near)
                    spreading.append(near)
        if not spreading:
            break
        trees -= len(spreading)
        burning = spreading
        minutes += 1
    return minutes if trees == 0 else -1
```

This is a breadth-first search from every fire at once. Each minute's trees are the ones whose shortest way from any fire takes that many steps, so each tree is set alight in the minute it would really catch, and it's handled only then. The time and space are in proportion to the squares.

Searching from each fire on its own and keeping the soonest time for each tree gives the same answer, with a search for every fire. Redrawing the whole map each minute is the slow way, too: for the largest test that's {% $fig.minutes %} minutes, each looking at all {% $fig.squares %} squares, {% $fig.looks %} looks in all, while the fire itself reaches each square once.
