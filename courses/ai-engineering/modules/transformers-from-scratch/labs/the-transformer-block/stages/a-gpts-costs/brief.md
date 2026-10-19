Before the app's team trains a model, it wants to know what each candidate would cost: how many parameters it holds, which sets its size on the device, and how many multiply-adds it takes for each token it reads, and for each token it learns from, which set how fast it writes and how long it takes to train. All three follow from the configuration. GPT-2 small holds {% $fig.small %} parameters, and GPT-3's largest model, {% $fig.gpt3_layers %} blocks of {% $fig.gpt3_width %} reading {% $fig.gpt3_context %} tokens, holds {% $fig.gpt3 %}: far too many to build on a laptop, but not to count.

In `costs.py`, write `costs(vocab, context, width, layers, heads, length)`, which gives a dict of three whole numbers for a GPT built as in stage 3:

- `parameters`, all its parameters, the tied output layer counted once;
- `forward`, the multiply-adds of a forward pass over a story of `length` tokens, divided by `length`;
- `training`, the multiply-adds of that forward pass and the backward pass that gives every parameter's gradient, divided by `length`.

Count the multiply-adds of every matrix multiply, as PyTorch's `FlopCounterMode` counts them, halved, since it counts a multiply and an add as two operations. Attention's scores and values count in full, though half the scores are masked. Work them out from the configuration: don't build a model.

```
costs(vocab, context, width, layers, heads, length) -> {"parameters": ..., "forward": ..., "training": ...}
```

Two tests run on every attempt. Then three checks run before the code ships.
