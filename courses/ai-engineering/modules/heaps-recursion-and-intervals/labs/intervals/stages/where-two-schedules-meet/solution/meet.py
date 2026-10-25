def common(first, second):
    found = []
    i = j = 0
    while i < len(first) and j < len(second):
        start = max(first[i][0], second[j][0])
        end = min(first[i][1], second[j][1])
        if start <= end:
            found.append((start, end))
        if first[i][1] < second[j][1]:
            i += 1
        else:
            j += 1
    return found
