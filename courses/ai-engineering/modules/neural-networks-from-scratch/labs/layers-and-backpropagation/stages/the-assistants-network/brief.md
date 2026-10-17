The office asked an assistant for the same network, and the assistant wrote `network.py`. Its five tests all pass.

Review it as if the office were about to train with it: fix every problem you can find, and keep what it does right. Four hidden checks test it the way training will use it. A run shows how many pass. You see which ones when you finish the review.

The office's request:

- `Linear`, `ReLU`, `cross_entropy` and `Network`, as in stages 1 to 3.
- Gradients right for a batch of any size, and for a network of any number of layers.
- A finite loss and gradient for logits of any size.
- Each backward pass's gradients, step after step, as training takes them.
