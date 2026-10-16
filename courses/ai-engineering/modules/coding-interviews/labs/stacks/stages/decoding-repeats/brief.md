In an encoded text, `count[part]` stands for `part` written `count` times. Write `decode`:

```
decode(text) -> text with each count[part] written out, inner ones first
```

`decode("3[ab]2[c]")` returns `"abababcc"`, and `decode("x2[y3[z]]")` returns `"xyzzzyzzz"`. A count can have several digits, as in `"10[a]"`. The texts hold lower-case letters, digits only in counts, and brackets that always close.
