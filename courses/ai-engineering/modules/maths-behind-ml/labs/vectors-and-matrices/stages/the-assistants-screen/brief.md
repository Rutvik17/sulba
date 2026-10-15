The clinic asked an assistant to put your steps together into a screen its system can call, and the assistant wrote `screen.py`. Its four tests all pass.

Review it as if the clinic were about to rely on it: fix every problem you can find, and keep what it does right. Four hidden production checks test it the way the clinic's system will use it. A run shows how many pass. You see which ones when you finish the review.

The clinic's request:

- Standardize the records and the new samples with the records' mean and standard deviation.
- Score each new sample by how far it lies past the midpoint of the two class means, toward the average malignant record, in standard deviations along the direction between them. Above 0, the malignant mean is nearer.
- For each new sample, give its `k` nearest records, nearest first, and their distances, worked out from the dot products.
