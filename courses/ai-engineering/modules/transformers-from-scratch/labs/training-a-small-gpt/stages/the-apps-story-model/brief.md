The team will train the app's model again each time the stories change, on a laptop, so it gives a training run a budget: `$\fig{budget}$` multiply-adds, as PyTorch counts them. Within it, the model must reach a loss of {% $fig.target %} or less on the validation stories, and write stories that end.

In `story.py`, write:

- `make()`, the app's GPT, untrained, for the stories' vocabulary of {% $fig.vocab %} tokens. Its context, width, blocks and heads are yours to choose.
- `fit(model, tokens, generator)`, which trains the model on the training stories' tokens with your `batches` and your `train`, drawing its batches with the `generator`, and gives the model back.

```
make() -> GPT
fit(model, tokens, generator) -> the model
```

The checks train the model `make()` gives with `fit` once, counting every multiply-add with PyTorch's `FlopCounterMode`. On the CPU, PyTorch's attention runs as one operation the counter doesn't see into, so the checks run it as matrix multiplies, which it counts. The model `make()` gives now, {% $fig.width_0 %} wide with {% $fig.layers_0 %} blocks and a context of {% $fig.context_0 %}, would read {% $fig.read_0 %} tokens within the budget.
