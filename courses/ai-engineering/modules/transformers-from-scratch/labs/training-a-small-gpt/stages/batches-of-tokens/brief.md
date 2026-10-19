The model learns by guessing each next token of the stories. What it reads is one long stream of tokens, cut into windows.

First, hold some stories back, to measure the model on stories it never trained on: every tenth story, {% $fig.validation %} of them, leaving {% $fig.training %} to train on. Each is held back whole, so no part of it reaches training, and from here on the vocabulary is learnt from the training stories alone.

GPT-3 put its documents into its context the same way: one after another, each followed by the end-of-text token, in windows of the full context that run across the separators, with nothing masked. From the separator, the model learns that what follows it is a new story.

In `data.py`, write:

- `split(stories)`, the stories to train on and the stories to validate with: every tenth story, the tenth, the twentieth and so on, to validate with, and the rest to train on, each in their order.
- `corpus(stories, merges)`, the stories' tokens as one tensor of `torch.long`, each story followed by the separator.
- `batches(tokens, length, size, generator)`, a generator that yields batches forever, each a pair `(inputs, targets)` of `size` windows of `length` tokens, the targets the same windows one token on. The windows begin `length` tokens apart from the start, as long as a window and its last target fit. Each pass over the tokens takes all its windows in a new order, from `torch.randperm` with the `generator`, and leaves out those too few to fill a last batch, so a pass reads each window once.
- `evaluate(model, tokens, length, size=64)`, the model's mean loss a token: the cross-entropy of its logits against each next token, over every window of `tokens`, `length` tokens apart from the start, read `size` windows at a time. Read them in evaluation mode without gradients, and leave the model in the mode it was in.

```
split(stories) -> (training, validation)
corpus(stories, merges) -> tensor of tokens
batches(tokens, length, size, generator) -> iterator of (inputs, targets)
evaluate(model, tokens, length, size=64) -> float
```
