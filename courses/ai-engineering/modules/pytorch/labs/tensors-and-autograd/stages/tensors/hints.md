`np.loadtxt(path, delimiter=",", skiprows=1)` reads the file into one array of floats. `torch.from_numpy` makes it a tensor without copying it, and `.to(torch.int64)` converts a column.

---

`view` reads a tensor's memory with a new shape, without copying, and `-1` lets it work out one size from the others.

---

`transpose(1, 2)` swaps each grid's rows and columns by swapping their strides, the steps through memory from one value to the next. The result isn't contiguous, so `view` can't flatten it, and `reshape` copies when it must.

---

`train.mean(dim=0)` and `train.std(dim=0)` give each pixel's mean and spread. PyTorch's `std` divides by `$n - 1$` unless told otherwise, and NumPy's by `$n$`.
