The clinic asked an assistant to put the model into production, and the assistant wrote `screener.py` with scikit-learn, as you would at work. Its three tests all pass.

Review it as if it were about to be used in the clinic: fix every problem you can find, and keep what it does right. Five hidden production checks test what the clinic will really do with it, and hold it to the model you built in stages 1 to 3. Each run tells you how many pass; you see which ones when you finish the review.

The clinic's request:

- Fit it once on our records, then score new samples as they arrive, one at a time or in batches.
- Give the same scores as the model you validated.
- Never pass over a sample with a missing measurement silently.
