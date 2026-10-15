The clinic will train its network on batches like yours, and asked an assistant for the code that draws them. The assistant wrote `batches.py`: `Batches`, which gives each epoch's batches of row numbers, and its `average`, which averages a quantity worked out for each record, such as its loss or its gradient, over a batch. Its four tests all pass.

Review it as if the clinic were about to train with it: fix every problem you can find, and keep what it does right. Four hidden production checks test it the way training will use it. A run shows how many pass. You see which ones when you finish the review.

The clinic's request:

- Each epoch: every record once, in batches of `size` rows, the last one smaller when `size` doesn't divide `n`.
- A new random order each epoch, and the same batches for the same seed and epoch, so that a run can be repeated.
- `average`: the mean over a batch's rows, whatever the batch's size.
