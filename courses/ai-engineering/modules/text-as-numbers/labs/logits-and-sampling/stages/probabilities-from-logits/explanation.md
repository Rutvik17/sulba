```python
def log_softmax(logits):
    logits = np.asarray(logits, dtype=float)
    shifted = logits - np.max(logits, axis=-1, keepdims=True)
    return shifted - np.log(np.sum(np.exp(shifted), axis=-1, keepdims=True))


def softmax(logits):
    return np.exp(log_softmax(logits))


def shares(pairs):
    yes = np.exp(pairs["yes"] - pairs["lse"])
    no = np.exp(pairs["no"] - pairs["lse"])
    return pd.DataFrame({"yes": yes, "no": no, "other": 1 - yes - no})
```

Subtracting the largest logit `$m$` multiplies the top and the bottom of the fraction by `$e^{-m}$`, so no probability changes, and the largest power becomes `$e^0 = 1$`: nothing overflows, and the sum is at least 1, so its log is never `$-\infty$`. `log_softmax` stays in logs, where `np.log(softmax(logits))` would give `$-\infty$` for any probability too small for a float.

Of the {% $fig.pairs %} answers, Yes is the likeliest first token for {% $fig.first_yes %} and No for {% $fig.first_no %}. Together they take {% $fig.both_mean %} of the probability on average, and never less than {% $fig.both_min %}. The rest goes to tokens such as {% $fig.others %}, which start a longer reply. People labelled {% $fig.exact %} of the pairs exact matches, {% $fig.substitutes %} substitutes, {% $fig.complements %} complements and {% $fig.irrelevant %} irrelevant.

The {% $fig.top %} logits the file keeps for each answer take at least {% $fig.kept_min %} of its probability, so a softmax over them alone gives almost the same probabilities as `lse` does. Almost: it divides by their sum alone, so each probability comes out a little higher than its share of the whole vocabulary.
