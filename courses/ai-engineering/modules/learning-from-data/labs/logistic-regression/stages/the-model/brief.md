Start `model.py`. A logistic regression model gives each sample a score, a weighted sum of its features, and turns the score into a probability with the sigmoid.

Write `sigmoid` so that it works on a number and on an array. It must not overflow: `np.exp(1000)` is too large for a float. Then write `predict_proba`, which returns one probability per row of `X`.

The tests use the lab's data: {% $fig.n_train %} training samples and {% $fig.n_test %} test samples, each with {% $fig.n_features %} measurements of the cell nuclei in a sample. A label of 1 means malignant.
