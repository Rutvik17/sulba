A run of a text is an anagram of a word when it holds the same characters, as many times each, in any order. Write `anagram_starts`:

```
anagram_starts(text, word) -> the position where each run of text that's an anagram of word
    starts, in order
```

`anagram_starts("listen silent enlist", "inlets")` returns `[0, 7, 14]`. Runs can overlap: `anagram_starts("abab", "ab")` returns `[0, 1, 2]`. Every character counts, spaces included, and `word` holds at least one.

The tests' longest text has {% $fig.characters %} characters, searched for a word of {% $fig.length %}.
