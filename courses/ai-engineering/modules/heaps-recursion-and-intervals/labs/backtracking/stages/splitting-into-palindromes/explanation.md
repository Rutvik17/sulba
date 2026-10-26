```python
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
```

Each split's first part is a palindrome that starts the text, and the rest of it is a split of what's left. So the search tries each palindrome that starts at the current place and goes on from its end, and a part that isn't a palindrome ends that branch at once. A text of one letter {% $fig.repeated %} times splits {% $fig.splits %} ways, since every cut between letters leaves palindromes, so the answer itself can be that long.

Trying every set of cuts and keeping those whose parts are all palindromes is the slow way: {% $fig.cuts %} sets of cuts for the tests' text of {% $fig.letters %} letters, which splits one way.
