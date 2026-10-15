In the survey's next pointing, about {% $fig.one_in %} candidates are expected to be pulsars, where {% $fig.train_share %} of the training set are. A classifier's probabilities carry the share of pulsars it was fit on, so its own would run high there. By Bayes' rule, moving to another share multiplies the odds of a pulsar, `p / (1 - p)`, by the odds of the new share over the odds of the share the classifier was fit on.

Ship `Screen`. It fits the survey's classifier on the candidates it's given with `trained`, and gives each new candidate its probability of being a pulsar where `share` of the candidates are. The survey trusts the classifier's order, so only the probabilities may change. `follow_ups` returns the row numbers of the `budget` candidates most likely to be pulsars, most likely first.

```
Screen(X, y, share) -> screen, its classifier fit on these candidates
screen.probabilities(X) -> each candidate's probability of being a pulsar
screen.follow_ups(X, budget) -> row numbers, the most likely pulsar first
```

If you missed any of stage 4's problems, this stage starts from the fixed `report.py`. There are no hints. The tests are hidden: you see which pass, but not their inputs. Four more checks decide whether it ships.
