The help desk keeps each chunk's vector under its text, so when a page changes, only the chunks whose text changed are embedded again. This stage builds the chunker it will run on every page it adds or changes, in `chunker.py`:

- `chunks(text)` gives each chunk's place in the page, its first character and the one after its last, in order.

What the chunker must do:

- hold every word of a page once, in order, in chunks of at most {% $fig.most %} words, the size whose chunks found the most of each answer at {% $fig.budget %} words;
- cut a page between its blocks, but within a block of more than {% $fig.most %} words;
- keep the test questions' answers whole;
- send few chunks to be embedded again when a page changes;
- cut a page saved on Windows, or with spaces on its blank lines, as it cuts the page itself.

How it does so is yours to choose.

```
chunks(text) -> list of (start, end)
```

Two tests run on every attempt. Then six checks run before the code ships.
