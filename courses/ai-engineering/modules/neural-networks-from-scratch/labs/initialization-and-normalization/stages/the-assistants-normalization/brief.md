The office asked an assistant for PyTorch's normalization layers to train its deeper networks with, and the assistant wrote `normalization.py`. Its five tests all pass.

Review it as if the office were about to train with it, then read digits with the trained network: fix every problem you can find, and keep what it does right. Four hidden checks test it the way training and evaluation will use it. A run shows how many pass. You see which ones when you finish the review.

The office's request:

- `BatchNorm1d` and `LayerNorm`, as in stages 2 and 3, each giving PyTorch's outputs and gradients.
- Running estimates kept as PyTorch keeps them, and used in evaluation.
- In evaluation, a digit read alone gives the outputs it gives in any batch.
