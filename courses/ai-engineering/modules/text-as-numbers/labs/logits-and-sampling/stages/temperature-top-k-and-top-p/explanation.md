```python
def warp(logits, temperature=1.0, top_k=0, top_p=1.0):
    scaled = np.asarray(logits, dtype=float) / temperature
    if 0 < top_k < len(scaled):
        scaled[scaled < np.sort(scaled)[-top_k]] = -np.inf
    probabilities = softmax(scaled)
    if top_p < 1:
        order = np.argsort(-probabilities, kind="stable")
        above = np.cumsum(probabilities[order]) - probabilities[order]
        probabilities[order[1:][above[1:] >= top_p]] = 0.0
        probabilities /= probabilities.sum()
    return probabilities
```

Dividing the logits by `$T$` raises each probability to the power `$1/T$` before they're shared out again, so a temperature below 1 moves probability to the likeliest tokens, and one above 1 spreads it out. Top-k doesn't depend on the temperature, since dividing by a positive `$T$` keeps the logits in order. Top-p does: it reads the probabilities after temperature and top-k, and keeps the token that takes their running total to `$p$`.

At Qwen2.5-1.5B-Instruct's settings, top-p keeps one token for {% $fig.single %} of the {% $fig.pairs %} pairs, so the first token of its answer to them can't vary. For the other {% $fig.double %}, it keeps two, Yes and No, the less likely of them with {% $fig.second_mean %} of the probability on average and up to {% $fig.second_max %}. The chart shows how often a draw isn't the likeliest token as the temperature changes, with the top-p you choose.

With top-p at 1, a temperature of {% $fig.hot %} puts {% $fig.hot_other %} of the probability on tokens other than Yes and No, on average: a reply that starts with neither. At the model's own settings, top-p removes every such token, for every pair.
