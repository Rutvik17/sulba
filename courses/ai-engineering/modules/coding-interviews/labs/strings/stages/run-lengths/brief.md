A run is a stretch of one character repeated. Write `encode` and `decode`:

```
encode(text) -> each run as its character followed by its length
decode(encoded) -> the text that encode gave encoded
```

`encode("aaabccdddd")` returns `"a3b1c2d4"`, and `decode("a3b1c2d4")` returns `"aaabccdddd"`. A run can be longer than nine, so a length can take several digits: `encode("x" * 12)` returns `"x12"`. The texts hold no digits.

The tests' longest text has {% $fig.characters %} characters.
