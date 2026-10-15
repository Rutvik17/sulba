Start `boost.py`. A forest grows its trees apart and averages them. Gradient boosting grows its trees one after another, each fitted to what the trees before it got wrong, and adds them up.

The model scores each call with a log-odds of yes, `$\log \frac{p}{1 - p}$` for a share of yes `$p$`. It starts every call at the log-odds of the training calls' share of yes. Then, round after round:

1. each call's share is `expit` of its log-odds, from `scipy.special`;
2. each call's residual is what it said, 1 for yes and 0 for no, less its share;
3. a regression tree, `DecisionTreeRegressor(criterion="friedman_mse", max_depth=depth, random_state=0)`, is fitted to the residuals;
4. each of the tree's leaves gets the value `$\sum (y - p) / \sum p(1 - p)$` over its calls;
5. each call's log-odds grows by `rate` times the value of its leaf.

Write `start`, `boost` and `boost_score`:

```
start(said_yes) -> the log-odds of the share of yes
boost(X, said_yes, rounds, rate, depth) -> a model
boost_score(model, X) -> each row's log-odds of yes
```

The model is a dict: `"start"`, `"rate"`, `"trees"`, the trees in turn, and `"values"`, for each tree an array of its leaves' values, indexed by node as `tree.apply` numbers them. The tests compare your scores of the training calls with scikit-learn's `GradientBoostingClassifier`, which boosts the same way.
