```python
from collections import deque


def letter_order(words):
    letters = list(dict.fromkeys(letter for word in words for letter in word))
    after = {letter: set() for letter in letters}
    for first, second in zip(words, words[1:]):
        for a, b in zip(first, second):
            if a != b:
                after[a].add(b)
                break
        else:
            if len(first) > len(second):
                return ""
    waiting_on = dict.fromkeys(letters, 0)
    for followers in after.values():
        for letter in followers:
            waiting_on[letter] += 1
    ready = deque(letter for letter in letters if waiting_on[letter] == 0)
    order = []
    while ready:
        letter = ready.popleft()
        order.append(letter)
        for later in after[letter]:
            waiting_on[later] -= 1
            if waiting_on[later] == 0:
                ready.append(later)
    return "".join(order) if len(order) == len(letters) else ""
```

Two neighbouring words agree up to the first place they differ, and the letter there in the first comes before the letter in the second: that's all the pair says, since the letters after it don't count. A pair that never differs is a word and a word it begins, which sorts only if the shorter comes first. The rules make a graph of letters, and Kahn's algorithm takes a letter once every letter before it is taken; a loop of rules leaves letters it can't take, and then no order exists. Neighbours are enough: if each word sorts after the one before it, every word sorts after every word before it, so comparing every pair finds no rule the neighbours miss. It takes time in proportion to the words' letters.

Comparing every pair of words is the slow way: for the longest test's {% $fig.words %} words, that's {% $fig.pairs %} pairs.
