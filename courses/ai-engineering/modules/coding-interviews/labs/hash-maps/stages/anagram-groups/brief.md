Two words are anagrams when one's letters can be rearranged into the other. Write `anagram_groups`:

```
anagram_groups(words) -> the words grouped with their anagrams, each group in the order its
    words appear, and the groups in the order of their first words
```

```python
anagram_groups(["listen", "stone", "silent", "notes", "enlist", "tones", "rat"])
# [["listen", "silent", "enlist"], ["stone", "notes", "tones"], ["rat"]]
```

Words are in lower case, `a` to `z`, and a word repeated is in its group twice. The tests' longest list has {% $fig.words %} words.
