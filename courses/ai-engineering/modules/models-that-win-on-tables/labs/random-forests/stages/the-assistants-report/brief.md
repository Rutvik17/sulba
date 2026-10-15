The forest's report to the bank was written by an assistant: `report.py`, whose `run` grows a forest on the training calls and reports two things: the AUC to expect on new calls, estimated out of bag, and how far the AUC on the validation calls falls when each column's values are shuffled. Its four tests all pass.

Review it as if the report went to the bank tomorrow: fix every problem you can find, and keep what it does right. Four hidden production checks test it the way it will be used. A run shows how many pass. You see which ones when you finish the review.

What the report must do:

- grow each tree on a bootstrap sample of its own;
- estimate the AUC with each training call scored only by the trees that left it out;
- measure each column's importance on the validation calls;
- come out the same each time it runs.
