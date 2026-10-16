The shop sends its product titles to a language model, and the model reads them as tokens: numbers from a fixed vocabulary, each standing for a run of bytes. This lab builds the shop's own tokenizer with a byte-pair encoding, which learns its vocabulary from text. It starts from the 256 bytes and merges the pair of neighbouring tokens that occurs most often into a new token, again and again.

First it splits the text into pieces with GPT-2's pattern, `PATTERN` in the starter: a word with the space before it, a number, a run of punctuation marks, or spaces. Merges happen within pieces, so no token runs from one word into the next.

Start `bpe.py`. Write `train`:

```
train(texts, merges) -> ranks, a dict from each token's bytes to its rank
```

The 256 bytes come first, each ranked by its value: `bytes([b])` has rank `b`. Then each merge counts every pair of neighbouring tokens within the pieces of all the texts, joins the commonest pair into one token wherever it occurs, from left to right, and gives the new token the next rank. When pairs tie, the one that occurs first in the texts merges. Stop early if no piece has two tokens left.

The tests compare yours with the trainer in tiktoken, OpenAI's tokenizer library. The shop's tokenizer, in `data/vocabulary.csv`, holds the {% $fig.merges %} merges learnt from the {% $fig.titles %} training titles in `data/titles.csv`: {% $fig.size %} tokens in all.
