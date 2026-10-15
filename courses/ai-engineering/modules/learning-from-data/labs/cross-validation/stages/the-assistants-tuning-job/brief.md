The plant asked an assistant to turn your cross-validation into its tuning job, and the assistant wrote `tuning.py`. Its three tests all pass.

Review it as if the plant were about to rely on it: fix every problem you can find, and keep what it does right. Four hidden production checks test it the way the plant will use it, against the cross-validation you built in stages 1 to 3. A run shows how many pass. You see which ones when you finish the review.

The plant's request:

- Choose the degree and penalty by five-fold cross-validation over our records, as you did.
- Fit the chosen model on every record.
- Say how far off it will be on mixes we haven't made yet. Our table's set 2, the test set, stands in for those mixes and stays out until the end.
