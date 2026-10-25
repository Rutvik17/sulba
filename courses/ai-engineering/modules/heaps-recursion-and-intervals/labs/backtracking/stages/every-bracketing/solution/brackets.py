def bracketings(pairs):
    found, chosen = [], []

    def extend(opened, closed):
        if closed == pairs:
            found.append("".join(chosen))
            return
        if opened < pairs:
            chosen.append("(")
            extend(opened + 1, closed)
            chosen.pop()
        if closed < opened:
            chosen.append(")")
            extend(opened, closed + 1)
            chosen.pop()

    extend(0, 0)
    return found
