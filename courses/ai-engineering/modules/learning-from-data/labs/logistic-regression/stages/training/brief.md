Train the model.

`standardize` rescales both sets with the training set's column means and standard deviations, so every column of the training set has mean 0 and standard deviation 1. The test set uses the training set's numbers, not its own.

`train` starts from zero weights and takes `steps` steps of gradient descent, `w = w - lr * dw` and `b = b - lr * db`. After each step it records the loss with its l2 term, and it returns `(w, b, losses)`.

With the default `lr` and `steps`, and `l2 = 1 / {% $fig.n_train %}`, your model must give the same probabilities as scikit-learn's `LogisticRegression(tol=1e-12)`, within 0.0001 on every test sample.
