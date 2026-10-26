```python
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
```

Two intervals share the numbers from the later of their starts to the earlier of their ends, when that start is no later than that end. Of the two intervals at the lists' places, the one that ends first can't meet anything after the other, since those start later still, so its list moves on. Each step moves a place along, so the walk takes time in proportion to the two lists' lengths together.

Comparing every interval of one list with every interval of the other is the slow way: {% $fig.pairs %} pairs for the longest test.
