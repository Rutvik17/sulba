```python
train_scaled, validation_scaled = scale(train, validation)
neighbours = nearest(train_scaled, validation_scaled, max(ks))
shares = [
    (vote(varieties, neighbours[:, :k]) == validation_varieties).mean() for k in ks
]
best = max(shares)
return shares, min(k for k, share in zip(ks, shares) if share == best)
```

The training beans can't choose `k`. Each training bean is its own nearest neighbour, at a distance of nothing, so with one neighbour the line names every training bean right, and the fewer neighbours vote, the better the training beans look. The validation beans aren't in the training set, so they show what each `k` does with beans the line hasn't seen: {% $fig.one %} named right with one neighbour, rising to {% $fig.best_share %} with {% $fig.best %}. One neighbour follows any single bean, an odd one included; many neighbours bring in beans farther away, of other varieties too.

The best of {% $fig.tries %} tries on the validation beans is an optimistic guide to the line's accuracy, since the choice was made to suit them. The test beans, whose `set` is 2, took no part in it: with {% $fig.best %} neighbours, the line names {% $fig.test %} of them right.
