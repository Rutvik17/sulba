`torch.optim.LBFGS(probe.parameters(), max_iter=1000, tolerance_grad=1e-9, tolerance_change=0, line_search_fn="strong_wolfe")` takes up to `max_iter` steps in one call of `optimizer.step(closure)`. `closure` zeroes the gradients, works out the loss, calls `loss.backward()` and gives back the loss.

---

`F.cross_entropy(scores, kinds)` is the mean cross-entropy over the tiles, and `probe.linear.weight.square().sum()` the sum of the squares of the weights.

---

`torch.bincount(kinds * count + given, minlength=count * count)` counts each pair of a tile's kind and the kind it's given, and `.reshape(count, count)` sets the counts out in rows.
