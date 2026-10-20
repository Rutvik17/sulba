The help desk will change its search only through a release check, run on the test questions before each change. In `release.py`, write `check(current, candidate, judgments, first, services, rng)`, which gives a `Release` for a candidate search against the current one, with your measures, `as_seen`, `relevant_texts` and `randomization_test`:

- `hit_rate` and `ndcg`: each search's hit rate at {% $fig.k %} and nDCG at {% $fig.depth %}, the current search's first, over every question in `judgments`, a question a search shows nothing for scoring 0, each judged as a reader sees its passages.
- `p`: the randomization test's p-value of the difference in hit rate at {% $fig.k %}, with {% $fig.repeats %} resamples drawn from `rng` in one call, the questions in the order of `judgments`.
- `services`: each service's two hit rates at {% $fig.k %}, the current search's first, over its own questions.
- `held`: the services whose hit rate at {% $fig.k %} falls by more than {% $fig.fall %}, in alphabetical order.
- `ship`: whether the candidate replaces the current search. It does when its hit rate at {% $fig.k %} is higher, the p-value is below {% $fig.level %}, and `held` is empty.

`judgments` maps each question to its relevant passages, `first` maps each passage to its text's first passage, and `services` maps each question to its service, as `data/questions.csv` names it.

```
check(current, candidate, judgments, first, services, rng) -> Release
```

Two tests run on every attempt. Then six checks run before the code ships.
