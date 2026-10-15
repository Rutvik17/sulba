The clinic asked an assistant to put your steps together into one search its system can call, and the assistant wrote `search.py`. Its four tests all pass.

Review it as if the clinic were about to rely on it: fix every problem you can find, and keep what it does right. Four hidden production checks test it the way the clinic's system will use it. A run shows how many pass. You see which ones when you finish the review.

The clinic's request:

- Standardize the records and the new samples with the records' mean and standard deviation, as your `standardize` does.
- For each new sample, give its `k` nearest records, nearest first, their distances, and the share of them that are malignant.
- New samples come in batches of any size, one sample included, and the system keeps the arrays it passes in to use again.
