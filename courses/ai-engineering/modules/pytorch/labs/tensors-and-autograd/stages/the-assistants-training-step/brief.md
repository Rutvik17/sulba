The office asked an assistant to port the training step too, and the assistant wrote `trainer.py`. Its four tests all pass.

Review it as if the office were about to train with it: fix every problem you can find, and keep what it does right. Four hidden checks test it the way the office will use it. A run shows how many pass. You see which ones when you finish the review.

The office's request:

- `start`, `scale`, `forward` and `step`, doing what your `network.py` and `digits.py` do.
- Every layer trained, step after step, as the NumPy reader trains it.
- Pixels scaled exactly as the NumPy reader scales them, so the port's numbers match the NumPy reader's.
- The start it's given kept as it was, so the office can train again from it.
