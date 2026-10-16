```python
def sample(probabilities, rng):
    totals = np.cumsum(probabilities)
    return int(np.searchsorted(totals / totals[-1], rng.random(), side="right"))


def answers(tokens, logits, rng, temperature=1.0, top_k=0, top_p=1.0):
    return [
        row[sample(warp(values, temperature, top_k, top_p), rng)]
        for row, values in zip(tokens, logits, strict=True)
    ]
```

The running totals split the range from 0 to 1 into one stretch for each token, as long as its probability, and `$u$` lands in a token's stretch with exactly that probability. `side="right"` takes the first total strictly greater than `$u$`, so a stretch of length 0 is never chosen.

At Qwen2.5-1.5B-Instruct's settings, the {% $fig.single %} pairs that keep one token get the same answer every time. Two draws for a pair differ with probability

```math
1 - \sum_i p_i^2
```

which adds up to {% $fig.expected %} over the {% $fig.pairs %} pairs. Drawing every pair's answer twice from one generator, seeded with {% $fig.seed %}, gave {% $fig.changed %} pairs a different answer the second time. A judge drawn this way gives the shop a different verdict on some pairs each time it runs.
