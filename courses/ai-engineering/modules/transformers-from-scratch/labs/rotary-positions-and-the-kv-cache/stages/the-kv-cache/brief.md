SmolLM2 writes a story a token at a time, and each token reads every token before it. Run as a full pass for each new token, it reads the whole story again each time, though the keys and values of the tokens already read never change, since no token reads a later one. A KV cache keeps them, so each step reads only the new tokens.

`Cache` holds, for each block, the keys and values of every token read so far: a tensor (kv_heads, length, 64) of keys, already rotated, and one of values. In `cache.py`, write:

- `step(model, tokens, cache)`, the logits (length, vocab) for `tokens`, the tokens that follow those the cache holds. It runs `model`'s own parts, adds the new tokens' keys and values to the cache, and lets each new token read every cached token and the new ones up to itself. The new tokens' positions carry on from `len(cache)`.
- `generate(model, prompt, steps)`, the tokens `model` writes after `prompt`, each the likeliest, until it writes `END`, which it keeps, or has written `steps` tokens. One `step` reads the prompt, and each later `step` reads the token just written.

```
step(model, tokens, cache) -> logits (length, vocab)
generate(model, prompt, steps) -> [token, ...]
```

The tests compare your logits, read in pieces of different lengths, with the full pass in float64, and your stories with the ones transformers writes.
