def splits(text):
    found, chosen = [], []

    def extend(start):
        if start == len(text):
            found.append(list(chosen))
            return
        for end in range(start + 1, len(text) + 1):
            part = text[start:end]
            if part == part[::-1]:
                chosen.append(part)
                extend(end)
                chosen.pop()

    extend(0)
    return found
