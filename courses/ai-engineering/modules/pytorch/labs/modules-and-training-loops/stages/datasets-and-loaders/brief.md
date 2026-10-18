The office's training reads its digits in batches, as PyTorch code does: a dataset gives one digit at a time, and a data loader deals them out. In `data.py`, write:

- `Digits(pixels, digits)`, a map-style `Dataset` that keeps them as `pixels` and `digits`: its length is the number of digits, and item `i` is digit `i`'s pixels and the digit it shows.
- `sets(path)`, the digits in the CSV file at `path` as three `Digits`: the training, validation and test sets, the rows whose first column is 0, 1 and 2, with pixels as `float64` and digits as `int64`.
- `batches(digits, seed)`, the office's training batches: a `DataLoader` that deals `digits` in batches of {% $fig.batch %}, in a new order each epoch, drawn from its `generator`, a `torch.Generator` of its own seeded with `seed`.
- `evaluate(reader, digits)`, the reader's mean cross-entropy over `digits`, as a float, and how many of them it reads right, as an int. It reads them in evaluation mode, records nothing for a backward pass, and leaves the reader in the mode it found it in.

```
Digits(pixels, digits)[i] -> (pixels, digit)
sets(path) -> (train, validation, test)
batches(digits, seed) -> a DataLoader
evaluate(reader, digits) -> (loss, right)
```
