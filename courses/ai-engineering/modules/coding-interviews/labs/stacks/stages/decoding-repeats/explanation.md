```python
def decode(text):
    stack = []
    current, count = "", 0
    for character in text:
        if character.isdigit():
            count = count * 10 + int(character)
        elif character == "[":
            stack.append((current, count))
            current, count = "", 0
        elif character == "]":
            before, times = stack.pop()
            current = before + current * times
        else:
            current += character
    return current
```

`current` is the text being built at the current depth, and `count` the number being read. At `[`, both wait on the stack while the part inside is built from nothing. At `]`, the part is repeated and added to the text that waited, so inner parts are written out before the parts around them. Each digit adds itself to `count`, which reads a count of several digits.

The time grows with the length of the decoded text, since every character of it is written, and the stack holds one entry for each bracket still open.
