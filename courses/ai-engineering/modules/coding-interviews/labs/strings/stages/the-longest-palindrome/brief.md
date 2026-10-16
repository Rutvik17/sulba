Write `longest_palindrome`:

```
longest_palindrome(text) -> the longest run of adjacent characters in text that reads the same
    forwards and backwards
```

`longest_palindrome("abacabad")` returns `"abacaba"`. When several runs tie for the longest, return the one that starts first, so `longest_palindrome("abcd")` returns `"a"`. An empty text gives `""`. Every character counts here, case and spaces included.
