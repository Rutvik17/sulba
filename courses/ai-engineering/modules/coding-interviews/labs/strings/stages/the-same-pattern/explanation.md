```python
def same_pattern(first, second):
    if len(first) != len(second):
        return False
    forward, backward = {}, {}
    for a, b in zip(first, second):
        if forward.setdefault(a, b) != b or backward.setdefault(b, a) != a:
            return False
    return True
```

`forward` keeps what each character of `first` was renamed to, and `backward` which character each character of `second` came from. `setdefault` adds the pairing the first time a character comes up and gives back the one already there after that, so a character renamed two ways fails the first check, and two characters renamed to the same one fail the second. One pass, with time in proportion to the texts and space in proportion to the characters they use.

Comparing where each character first appears, with `first.index(character)`, says the same thing but searches the text again for every character: up to {% $fig.searched %} characters searched for the longest test, far past the time limit.
