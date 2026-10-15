The survey asked an assistant to turn your measures into a report it can plan with, and the assistant wrote `report.py`. Its four tests all pass.

Review it as if the survey were about to rely on it: fix every problem you can find, and keep what it does right. Four hidden production checks test it the way the survey will use it, against the measures you built in stages 1 to 3. A run shows how many pass. You see which ones when you finish the review.

The survey's request:

- Train the classifier on the training set: logistic regression on standardized measurements.
- Measure it on the test set, which stands in for a night's candidates: its ROC AUC, and the share of pulsars among the candidates it flags at {% $fig.threshold %}.
- Say how many pulsars to expect among the test set's {% $fig.test %} candidates.
