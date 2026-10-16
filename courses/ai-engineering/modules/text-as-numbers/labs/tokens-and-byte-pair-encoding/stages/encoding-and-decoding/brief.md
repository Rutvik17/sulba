With its vocabulary, the tokenizer turns a title into tokens. It splits the title into pieces with the pattern, turns each piece into its bytes, and then, within each piece, merges the neighbouring pair whose joined bytes are the token of lowest rank, until no neighbouring pair joins into a token. That replays, piece by piece, the merges training made, in the order it made them. A token is given as its rank.

Decoding turns tokens back into text: it joins the tokens' bytes and reads them as UTF-8. A token's bytes needn't make whole characters. In UTF-8 a character outside ASCII takes two to four bytes, and a merge can leave them in different tokens. So join every token's bytes before reading any, and read bytes that don't make a whole character as U+FFFD, the replacement character, as `bytes.decode(errors="replace")` does.

`load_vocabulary` in the starter reads the shop's tokenizer from `data/vocabulary.csv`. Write `encode` and `decode`:

```
encode(text, ranks) -> the text's tokens, a list of ranks
decode(tokens, ranks) -> the text they stand for
```

The tests compare yours with tiktoken's encoder, made with the shop's vocabulary, on titles from all three shops.
