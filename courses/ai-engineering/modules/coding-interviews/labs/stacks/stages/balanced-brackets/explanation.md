```python
def balanced(text):
    pairs = {")": "(", "]": "[", "}": "{"}
    opened = []
    for character in text:
        if character in "([{":
            opened.append(character)
        elif character in pairs:
            if not opened or opened.pop() != pairs[character]:
                return False
    return not opened
```

The last bracket opened is the first that must close, which is the order a stack gives back. A closing bracket fails when nothing is open or the top is another kind, and a text ends balanced only when nothing is left open. Each character is pushed and popped at most once: time in proportion to the text, and space up to the deepest nesting.

Removing each `()`, `[]` and `{}` until none is left gives the same answer, but each pass over the text removes only the pairs that touch: for the longest test, brackets nested {% $fig.depth %} deep, that's {% $fig.passes %} passes reading {% $fig.read %} characters, far past the time limit.
