The help desk asked an assistant for a scorecard of its agents before you started. The assistant wrote `scorecard.py`, whose `scorecard` gives each agent's line from `runs.csv`'s rows: pass^1 and pass^k over the tasks, and the median and 90th percentile of the tasks' seconds and tokens, each with its interval. It uses your `quantile` and `interval` from `costs.py`. Its four tests all pass.

Review it as if the help desk were about to choose an agent by it: fix every problem you can find, and keep what it does right. Four hidden checks test it the way the help desk will use it. A run shows how many pass. You see which ones when you finish the review.

What the code must do:

- estimate a task's pass^k from its trials, as the chance that k of them, drawn without replacement, were all done;
- give each interval at the confidence asked, with half of what it leaves out beyond each end;
- count each task once in a percentile, by its median over its trials;
- count the cost of every run, whether it did its task or not.
