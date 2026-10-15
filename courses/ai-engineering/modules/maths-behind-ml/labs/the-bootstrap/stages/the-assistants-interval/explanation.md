The assistant's tests checked shapes and ranges: resamples of the right size, accuracies between 0 and 1, an interval inside the accuracies. A shuffled resample has the right shape. Accuracies against the wrong labels still lie between 0 and 1, and an interval too narrow, or with its ends reversed, still lies inside them.

---

An interval is checked against what it promises: resamples that repeat some samples and leave out others, accuracies that center on the one measured, quantiles that leave the stated share outside, and ends in order. Each of those is a test that needs no more than a few lines.
