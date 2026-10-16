Write `is_palindrome`:

```
is_palindrome(text) -> whether text's letters and digits read the same forwards and backwards,
    ignoring case and every other character
```

`is_palindrome("Step on no pets!")` returns `True`, and `is_palindrome("Hello, world")` returns `False`. Letters and digits are the characters `str.isalnum` counts, and a text with none of them reads the same both ways.

The tests' longest text has {% $fig.characters %} characters. Solve it without copying the text.
