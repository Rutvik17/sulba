def islands(rows):
    """The number of islands on the map: groups of land squares, `#`, joined along their
    edges."""
    seen, count = set(), 0
    for top, row in enumerate(rows):
        for left, square in enumerate(row):
            if square != "#" or (top, left) in seen:
                continue
            count += 1
            seen.add((top, left))
            waiting = [(top, left)]
            while waiting:
                y, x = waiting.pop()
                for near in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
                    ny, nx = near
                    land = (
                        0 <= ny < len(rows)
                        and 0 <= nx < len(row)
                        and rows[ny][nx] == "#"
                    )
                    if land and near not in seen:
                        seen.add(near)
                        waiting.append(near)
    return count
