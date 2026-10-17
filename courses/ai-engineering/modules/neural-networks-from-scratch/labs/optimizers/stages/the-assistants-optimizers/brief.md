The office asked an assistant for PyTorch's optimizers to train its networks with, and the assistant wrote `optim.py`. Its five tests all pass.

Review it as if the office were about to train with it: fix every problem you can find, and keep what it does right. Four hidden checks test it the way training will use it. A run shows how many pass. You see which ones when you finish the review.

The office's request:

- `SGD` with momentum and weight decay, `Adam` and `AdamW`, each taking PyTorch's steps.
- A learning rate that a schedule can change between steps.
- Every step made to the network's own arrays.
