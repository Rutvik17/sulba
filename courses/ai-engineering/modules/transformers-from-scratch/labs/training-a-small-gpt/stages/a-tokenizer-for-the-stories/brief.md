The reading app's team is ready to train its model. It learns from TinyStories: short stories GPT-4 wrote in words a small child understands. The lab trains on {% $fig.stories %} of them, from one file of {% $fig.file_bytes %} bytes with `<|endoftext|>` between each story and the next.

A model reads tokens, and a vocabulary learnt from the stories themselves fits them closely. Write one with byte-pair merges, as in the Tokens and byte-pair encoding lab, with two changes: each merge is a pair of token numbers, and the separator is a token of its own.

In `tokenizer.py`, `PATTERN` and `END` are given. Write:

- `stories(path)`, the stories in the file at `path`, each without the spaces and newlines around it. The file starts partway through a story, at "{% $fig.opening %}", so leave out the text before its first separator, and any piece left empty.
- `train(stories, size)`, the merges for a vocabulary of `size` tokens, as a list of pairs in the order they're learnt. Tokens 0 to 255 are the bytes, merge `i` makes token `256 + i`, and the separator is the last token, `size - 1`, so there are `size - 257` merges. Split each story into pieces with `PATTERN`, and merge only inside a piece. Each merge joins the pair of tokens seen side by side most often across the stories, and of pairs seen as often, the one whose numbers come first: `(32, 99)` before `(97, 98)`. Stop early if no pair is left.
- `encode(text, merges)`, the text's tokens. Each `END` in the text is the token `256 + len(merges)`, and each piece of the text between is merged pair by pair, the pair learnt first going first.
- `decode(tokens, merges)`, the text the tokens stand for, with any bytes that don't make a character shown as U+FFFD.

```
stories(path) -> [str, ...]
train(stories, size) -> [(int, int), ...]
encode(text, merges) -> [int, ...]
decode(tokens, merges) -> str
```

The tests compare your merges with those you get by counting every pair again for each merge, then learn a vocabulary of {% $fig.size %} tokens from every story and encode them all.
