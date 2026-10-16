The shop's model reads only the first tokens of each title, up to a set limit, and drops the rest wherever the limit falls: inside a word, or inside a character. So the app will shorten each title itself before sending it, to cuts a reader can follow.

Write `shorten`:

```
shorten(title, limit, ranks) -> the title, cut to fit within limit tokens
```

- A title within the limit stays whole.
- A longer one is cut after its last whole piece that fits: the longest start of the title, in whole pieces, within the limit.
- When even its first piece is over the limit, as a long run of Japanese characters can be, it is cut inside that piece: the longest start of the piece within the limit, which can be no characters at all.

Count tokens with your `encode`. A longer start can take fewer tokens than a shorter one, when a merge joins its last character to the ones before it, so try every length.

Four hidden checks test `shorten` on titles from all three shops before it ships.
