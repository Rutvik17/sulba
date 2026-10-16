```python
def longest_unique(text):
    last = {}
    start = best = 0
    for position, character in enumerate(text):
        if last.get(character, -1) >= start:
            start = last[character] + 1
        last[character] = position
        best = max(best, position - start + 1)
    return best
```

The window from `start` to the current position never holds a character twice. When the new character was last seen inside the window, the window starts again just after that, which drops the earlier copy and nothing more than it must. A last position before `start` is outside the window, so it doesn't move it back. Each character is looked at once: time in proportion to the text, and space in proportion to the different characters.

Growing a run from every start until a character repeats reads up to {% $fig.reads %} characters for the longest test, far past the time limit.
