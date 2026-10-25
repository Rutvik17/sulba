```python
def parts(text):
    last = {letter: place for place, letter in enumerate(text)}
    sizes, start, end = [], 0, 0
    for place, letter in enumerate(text):
        end = max(end, last[letter])
        if place == end:
            sizes.append(end - start + 1)
            start = place + 1
    return sizes
```

A part that holds a letter has to reach that letter's last place, so the first part runs at least to its first letter's last place, and each letter met on the way can push that end further. When the walk reaches the end so far, every letter in the part has appeared for the last time, so a cut there is the earliest that works, and it leaves the most room for the parts after it. A dict of each letter's last place takes one pass over the text, and the walk another.

Trying each place to cut and checking whether a letter falls on both sides of it is the slow way: {% $fig.cuts %} places for the longest test, each a look over the whole text.
