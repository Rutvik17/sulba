def minutes_to_burn(rows):
    """The minutes until every tree has caught fire, or -1 if some tree never does."""
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
