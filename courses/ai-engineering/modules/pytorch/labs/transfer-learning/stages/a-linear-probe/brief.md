The survey's experts label {% $fig.labelled %} tiles of each kind. A linear probe learns the kinds from the backbone's features alone, with a linear layer that gives each kind a score: multinomial logistic regression on the features. `probe.py` starts with `Probe`, a linear layer on standardized features, each feature less its mean over the labelled tiles and divided by its standard deviation over them. Below it, write:

- `fit_probe(features, kinds, decay)`, a `Probe` for the labelled tiles' features and their kinds' numbers. It keeps the mean and standard deviation (`torch.std`'s) of each feature over them in `float64`, and has the weights and biases that minimize the tiles' mean cross-entropy plus `decay` times the sum of the squares of its weights, not its biases, found with `torch.optim.LBFGS`. Its kinds are numbered from 0 to the largest number in `kinds`.
- `accuracy(probe, features, kinds)`, the share of the tiles whose kind the probe gives right, its kind for a tile being the one with the highest score, and the share's standard error, `$\sqrt{p(1-p)/n}$` for a share `$p$` of `$n$` tiles.
- `confusion(probe, features, kinds)`, how many tiles of each kind the probe gives each kind, as an `int64` tensor with a row for each kind the tiles are and a column for each kind the probe gives them.

```
fit_probe(features, kinds, decay=1e-3) -> Probe
accuracy(probe, features, kinds) -> (share, standard error)
confusion(probe, features, kinds) -> int64 tensor (kinds, kinds)
```
