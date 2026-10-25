def symbol(row, place):
    if row == 1:
        return 0
    parent = symbol(row - 1, (place + 1) // 2)
    return parent if place % 2 else 1 - parent
