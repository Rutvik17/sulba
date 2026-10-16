To draw a token, generation picks one at random, each with its probability after `warp`. NumPy's `rng.choice(len(probabilities), p=probabilities)` draws by inverse transform: it adds up the probabilities in order, draws a number `$u$` uniformly from 0 up to 1 with `rng.random()`, and takes the first token whose running total is greater than `$u$`. A token with probability 0 adds nothing to the total, so it is never drawn.

Write:

```
sample(probabilities, rng) -> the index of the token drawn, as rng.choice draws it
answers(tokens, logits, rng, temperature=1.0, top_k=0, top_p=1.0) -> each pair's first token
```

`sample` takes one number from `rng` for each token it draws, so from a generator with the same seed it draws exactly what `rng.choice` would. `answers` draws for the pairs in order, all from the one `rng`, with the settings given.
