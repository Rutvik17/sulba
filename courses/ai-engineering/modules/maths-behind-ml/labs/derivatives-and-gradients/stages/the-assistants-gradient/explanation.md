The assistant's tests checked the gradient numerically, but at zero weights. There every hidden output is 0, so `$1 - A$` and `$1 - A^2$` are both 1, the hidden layer's inputs and outputs are the same, and there are no weights for the decay to shrink. Three of the four problems vanish at zero weights, and so does every slope except the output bias's. A step from zero weights lowers the loss whatever the other slopes say, and nothing pushed the network to be confident, so the loss never overflowed.

---

A gradient check is only as strong as the point it's taken at. At random weights every term has a value, so a wrong one shows. The decay can be checked on its own, as the difference between the gradients with and without it. And a loss is checked where training can take it: to scores far beyond any an untrained network gives.
