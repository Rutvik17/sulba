def all_opened(rooms):
    opened = {0}
    stack = [0]
    while stack:
        for key in rooms[stack.pop()]:
            if key not in opened:
                opened.add(key)
                stack.append(key)
    return len(opened) == len(rooms)
