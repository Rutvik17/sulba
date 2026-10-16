```python
def anagram_groups(words):
    groups = {}
    for word in words:
        groups.setdefault("".join(sorted(word)), []).append(word)
    return list(groups.values())
```

Anagrams, and only anagrams, have the same letters in sorted order, so the sorted letters make a key that gathers each group in a dict. A dict keeps its keys in the order they were first added, so the groups come out in the order of their first words, and each list in the order its words came.

Sorting a word of `k` letters takes time in proportion to `$k \log k$`, so the whole takes `$n k \log k$` for `n` words, and the dict holds every word once. Counting each word's letters into a tuple of 26 counts makes a key in time in proportion to `k` instead. Comparing every word with every other means {% $fig.pairs %} pairs for the longest test's {% $fig.words %} words, far past the time limit.
