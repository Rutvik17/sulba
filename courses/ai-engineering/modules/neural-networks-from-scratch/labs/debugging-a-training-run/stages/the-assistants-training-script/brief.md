The office asked an assistant for its training script, and the assistant wrote `train.py`. Its five tests all pass.

Review it as if the office were about to train its network with it: fix every problem you can find, and keep what it does right. Four hidden checks test it the way the office will run it. A run shows how many pass. You see which ones when you finish the review.

The office's request:

- `train`, which trains the network's own arrays on the training digits alone, for `steps` steps of SGD, and gives back each batch's loss.
- Each step from the mean of `accumulate` batches' gradients, as one batch of their combined size would give it, clipped as `clip_grad_norm_` clips gradients.
- The batches drawn in a new random order each time it has been through the training digits.
