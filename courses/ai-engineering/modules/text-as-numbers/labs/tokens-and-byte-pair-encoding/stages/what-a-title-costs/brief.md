A model reads a limited number of tokens at a time, and the work of reading a text grows with its tokens, so a title's cost is its tokens, not its characters. The shop sells in the US, Spain and Japan, and its tokenizer learnt its merges from US titles alone. `data/titles.csv` holds {% $fig.per_shop %} test titles from each shop.

Write `costs`:

```
costs(titles, ranks) -> a DataFrame with a row for each shop
```

`titles` is a table like `data/titles.csv`, with a `shop` and a `title` column. Each shop's row holds `characters`, the characters in all its titles, `tokens`, the tokens they take, and `per_token`, characters per token.

The chart shows characters per token in each shop's titles as the tokenizer keeps more of its merges, from none to all of them.
