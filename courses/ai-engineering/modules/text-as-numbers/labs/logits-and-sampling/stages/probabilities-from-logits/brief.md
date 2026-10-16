The shop shows a list of products for every search, and wants to know which of them match what the shopper asked for. It asks a small language model that runs on its own machine, Qwen2.5-1.5B-Instruct: "Does this product match the shopping query? Answer Yes or No.", followed by the query and the product's title.

To write a token, the model first gives every token in its vocabulary a score, its logit. Softmax turns the logits `$z$` into probabilities:

```math
p_i = \frac{e^{z_i}}{\sum_j e^{z_j}}
```

`data/logits.csv` holds {% $fig.pairs %} such questions about query and product pairs from Amazon's Shopping Queries Dataset, each with the label people gave the pair: E for an exact match, S for a substitute, C for a complement and I for irrelevant. For the first token of each answer, it keeps the {% $fig.top %} highest logits with their tokens, highest first; the logits of Yes and No, in `yes` and `no`; and in `lse`, the log of the sum below the line, taken over the whole vocabulary:

```math
\text{lse} = \log \sum_j e^{z_j}
```

So a token's probability is `$e^{z_i - \text{lse}}$`.

Start `judge.py`, where `load_pairs` in the starter reads the file. Write:

```
log_softmax(logits) -> the log of each probability, along the last axis
softmax(logits) -> the probabilities, along the last axis
shares(pairs) -> each pair's probability that its answer starts with Yes, No or another token
```

A float can't hold `$e^z$` once `$z$` passes {% $fig.overflow %}. Subtract the largest logit from every logit first: each probability stays as it was, and no power is above 1. A logit of `$-\infty$`, a token removed, has probability 0. The tests compare yours with SciPy's.
