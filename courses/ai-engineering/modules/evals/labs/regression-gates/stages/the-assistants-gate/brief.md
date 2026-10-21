The help desk asked an assistant for the gate its CI will run on each release before it ships. The assistant wrote `gate.py`: `gate`, which compares a candidate's scores with the baseline's on the test set and stops the candidate when its score is lower at level `alpha`, and `spread`, the standard error it uses. Its three tests all pass.

Review it as if the help desk were about to put it in CI: fix every problem you can find, and keep what it does right. Four hidden checks test it the way the help desk will use it, on its releases' replies. A run shows how many pass. You see which ones when you finish the review.

What the code must do:

- measure the change on every sample of each question;
- take the standard error from each question's difference between the releases;
- count each page's questions together;
- stop a release only when its interval lies wholly below zero, so that a release no worse than the baseline is stopped at most `alpha` of the time;
- give the interval from `change - z * error` to `change + z * error`, with the `z` that leaves `alpha` of the normal distribution above.
