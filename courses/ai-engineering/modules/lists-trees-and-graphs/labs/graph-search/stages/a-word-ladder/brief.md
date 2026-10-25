A word ladder climbs from one word to another a letter at a time: each word differs from the one before it in exactly one place. Write `ladder`:

```
ladder(start, end, words) -> the number of words in the shortest ladder from start to end,
    every word after start from words, or 0 if there's none
```

All the words have the same length, in lower case letters, and start and end differ. From `"cold"` to `"warm"` with these words, the shortest ladder has 5 words, such as cold, cord, card, ward, warm:

```
["cord", "card", "ward", "warm", "word", "worm", "corm", "wore", "core"]
```

`start` needn't be among `words`, but `end` must be, or there's no ladder. The tests' longest list has {% $fig.words %} words of {% $fig.letters %} letters.
