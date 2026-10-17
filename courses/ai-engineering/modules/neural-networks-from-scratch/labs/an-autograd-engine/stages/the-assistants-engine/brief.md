The office asked an assistant for an engine of tensors to train its networks with, and the assistant wrote `autograd.py`. Its five tests all pass.

Review it as if the office were about to train with it: fix every problem you can find, and keep what it does right. Four hidden checks test it the way networks will use it. A run shows how many pass. You see which ones when you finish the review.

The office's request:

- `Tensor`, `unbroadcast` and `topological_order`, as in stage 3.
- Gradients right for a tensor used more than once, directly or through the tensors made from it.
- Broadcasting as NumPy does it: of a number, a row or a column.
- Every operation's derivative right at every input where it's defined.
