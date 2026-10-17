The service needs one model, and two more were put forward. Both are now in `model.py`: `make_boosted()`, boosted trees, and `make_weighted()`, the logistic regression with the readmitted stays weighted up. Choose the model to ship, one of the three or one of your own, and add:

```
make_chosen() -> a new, unfitted pipeline of the model you ship
chosen(table) -> that model, fitted on every stay in table
```

Seed anything random with `SEED`, so the same stays always give the same model.

The planners add up the service's probabilities to know how many readmissions to expect. A request can bring any code in the ID mapping, including the {% $fig.unseen %} that no stay in the extract has. Three checks decide whether the model ships, and each run shows what they measured, so you can try each model in turn. There are no hints. The tests are hidden: you see which pass, but not their inputs.
