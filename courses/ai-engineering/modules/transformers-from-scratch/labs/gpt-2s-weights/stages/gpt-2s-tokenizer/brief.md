GPT-2 reads tokens, so before its weights can predict anything, text must become GPT-2's own tokens, from the tokenizer OpenAI published with the weights. It splits text with the pattern of the Tokens and byte-pair encoding lab and merges bytes pair by pair, and its merges come in two files:

- `data/vocab.json`, every token's string with its number.
- `data/merges.txt`, a first line naming its version, then one merge a line: its two strings with a space between, in the order they were learnt.

Their strings stand for bytes, with a character for each byte, so every merge can be written as text. The bytes that print as themselves in Latin-1, `!` to `~`, `¡` to `¬` and `®` to `ÿ`, keep their character. Each of the others, in the order of the bytes, takes the next character from U+0100 on, so a space becomes {% $fig.space %}.

In `tokenizer.py`, `PATTERN` and `END` are given. Write:

- `byte_characters()`, each byte's character, by the byte.
- `load(folder)`, the vocabulary, a dictionary from each token's string to its number, and the merges, a list of pairs of strings in the file's order.
- `encode(text, vocabulary, merges)`, the text's tokens. Each `END` in the text is a token of its own, number {% $fig.end %}. Each piece between, as `PATTERN` splits it, becomes the characters of its UTF-8 bytes. Then, again and again, the pair of neighbouring strings that comes first in the merges is joined, wherever it stands, until no pair left is a merge. Each string left is a token.
- `decode(tokens, vocabulary)`, the text the tokens stand for, with any bytes that don't make a character shown as U+FFFD.

```
byte_characters() -> {byte: character, ...}
load(folder) -> ({string: number, ...}, [(string, string), ...])
encode(text, vocabulary, merges) -> [int, ...]
decode(tokens, vocabulary) -> str
```

The tests compare your tokens with tiktoken's for texts in several languages, with numbers, contractions, runs of spaces and the separator.
