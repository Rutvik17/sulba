The judge sounds sure of itself. Of the {% $fig.val_sure %} validation pairs whose probability of Yes, among Yes and No, is at least {% $fig.sure_cut %}, {% $fig.val_sure_exact %} are exact matches; of the {% $fig.val_doubt %} with at most {% $fig.doubt_cut %}, {% $fig.val_doubt_exact %} are. The shop wants probabilities it can act on: of the pairs given a probability `$p$`, a share close to `$p$` should be exact matches.

Calibrate the judge on the {% $fig.validation %} validation pairs. Divide the margin between its Yes and No logits by a temperature `$T$`, as temperature divides logits, and add a shift `$b$`:

```math
P(\text{exact}) = \frac{1}{1 + e^{-\left((z_{\text{Yes}} - z_{\text{No}})/T + b\right)}}
```

Write:

```
match_probability(pairs, temperature=1.0, shift=0.0) -> each pair's probability of an exact match
calibrate(pairs) -> (temperature, shift) with the least log loss on the pairs' labels
```

A pair is an exact match when its label is E. With `temperature=1.0` and `shift=0.0`, `match_probability` is the judge's own probability of Yes among Yes and No. Import `minimize` from `scipy.optimize` at the top of `judge.py` to fit the two numbers.

Four hidden checks fit yours on the validation pairs, then test it on the {% $fig.test %} test pairs before it ships.
