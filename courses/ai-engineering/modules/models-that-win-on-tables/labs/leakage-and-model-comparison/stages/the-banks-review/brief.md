The bank will run this review every quarter as new calls come in, on candidates its analysts bring: other models and other settings. Each candidate's interval can mislead. A {% $fig.confidence %} interval is built to miss the true difference {% $fig.miss %} of the time, so among many candidates no better than the baseline, one will often seem to beat it. The review shares the confidence among them: with `$m$` candidates, each interval is at `$1 - (1 - c) / m$`, so that all of them hold together at least {% $fig.confidence %} of the time. A candidate beats the baseline when its whole interval lies above 0, and the bank ships the candidate that beats it by the most, or keeps the baseline.

The bank also wants to see how a model ranks calls made after the ones it learnt from. The calls are in the order they were made, and `latest` fits a model on the earlier calls and scores it on the last ones.

Write `review`, `choose` and `latest`:

```
review(scores, baseline, n_fit, n_held, confidence) -> a DataFrame with a row per candidate
choose(scores, baseline, n_fit, n_held, confidence) -> the name of the model to ship
latest(model, calls, said_yes, share) -> the model's AUC on the last share of the calls
```

`scores` is a table from `fold_scores`, and every model in it but the baseline is a candidate. `review`'s rows come in the candidates' order, with the columns `difference`, `low`, `high` and `beats`, the last True or False. `choose` returns the baseline if no candidate beats it, and the first of equal leads. `latest` fits a fresh copy of the model on all but the last `round(len(calls) * share)` calls, and returns its AUC on those.

There are no hints. The tests are hidden: you see which pass, but not their inputs. Four more checks decide whether it ships.
