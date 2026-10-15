The clinic will report its rule's accuracy with an interval, and asked an assistant for the code. The assistant wrote `evaluation.py`: `resample`, `resampled_accuracies`, which works out the accuracy of the predictions against the labels on each resample, and percentile and basic intervals of those accuracies. Its four tests all pass.

Review it as if the clinic were about to report with it: fix every problem you can find, and keep what it does right. Four hidden production checks test it the way the clinic will use it. A run shows how many pass. You see which ones when you finish the review.

The clinic's request:

- Resamples drawn with replacement, each as many samples as the clinic has.
- Each resample's accuracy: each prediction against its own sample's label.
- Percentile and basic intervals at any confidence, as SciPy's `bootstrap` gives them.
