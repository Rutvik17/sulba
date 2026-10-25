Write `splits`:

```
splits(text) -> every way to cut the text into parts that are all palindromes, each a list of
    its parts in order
```

A palindrome reads the same backwards, and every single letter is one. `splits("aab")` returns `[["a", "a", "b"], ["aa", "b"]]`, the splits in any order. The tests' longest text has {% $fig.letters %} letters.
