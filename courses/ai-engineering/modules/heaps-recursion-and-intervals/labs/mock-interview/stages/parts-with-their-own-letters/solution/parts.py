def parts(text):
    last = {letter: place for place, letter in enumerate(text)}
    sizes, start, end = [], 0, 0
    for place, letter in enumerate(text):
        end = max(end, last[letter])
        if place == end:
            sizes.append(end - start + 1)
            start = place + 1
    return sizes
