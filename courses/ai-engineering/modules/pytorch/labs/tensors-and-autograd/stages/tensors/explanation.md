A tensor is a block of memory and a way to read it: a shape, and a stride for each dimension, the number of values to step over to move one place along it. The office's pixels, held in a block of their own, are {% $fig.digits %} rows of {% $fig.pixels %} values, so each row starts {% $fig.pixels %} values after the one before. `view` reads the same memory with a new shape: the grids step {% $fig.pixels %} values from one digit to the next, {% $fig.side %} from one row of a grid to the next, and 1 along a row. Nothing is copied, so a change through the grids changes the pixels too.

`transpose` swaps two strides, so a transposed grid steps {% $fig.side %} values along a row and 1 down a column. Its values are no longer in reading order in memory, the tensor isn't contiguous, and no single stride can flatten a grid into a row, so `view` raises an error. `reshape` gives a view when one exists and a copy when it doesn't, and `contiguous()` makes the copy outright.

`torch.from_numpy` shares an array's memory in the same way, so a tensor made from the office's NumPy arrays changes them when it changes. `torch.tensor` copies.

The spread is where the port could quietly drift from the NumPy reader. For a pixel's `$n$` counts `$x_i$` with mean `$\mu$`:

```math
s = \sqrt{\frac{1}{n - c} \sum_i (x_i - \mu)^2}
```

PyTorch's `std` takes `$c = 1$`, Bessel's correction, unless `correction` says otherwise, and NumPy's `std` takes `$c = 0$` unless `ddof` does. Over the {% $fig.training %} training digits, PyTorch's default spread is {% $fig.factor %} times NumPy's, up to {% $fig.gap %} counts more. That's small, but every scaled pixel moves, and the port's numbers no longer match the NumPy reader's. The {% $fig.constant %} pixels that never vary in the training digits, both on the grid's edge and blank in every one, are divided by 1, as before.
