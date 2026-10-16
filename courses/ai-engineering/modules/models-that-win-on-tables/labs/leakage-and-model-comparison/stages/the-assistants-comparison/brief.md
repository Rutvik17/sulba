The bank asked an assistant to run the comparison, with one thing more: each model also reads the share of yes of a call's age and of its job and education pair, learnt with scikit-learn's `TargetEncoder`. The assistant wrote `report.py`, whose `run` gives each model's mean AUC and each other model's difference from the baseline, with an interval. Its four tests all pass.

Review it as if the bank were about to choose its model by it: fix every problem you can find, and keep what it does right. Four hidden production checks test it the way it will be used. A run shows how many pass. You see which ones when you finish the review.

What the comparison must do:

- learn each call's shares without its own answer, and the held-out calls' shares from the fit calls alone;
- score every model on the same folds;
- give each mean difference a standard error that allows for the calls the folds share;
- give {% $fig.confidence %} intervals.
