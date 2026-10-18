The records office's reader, the network you built in NumPy in the last module, is moving to PyTorch. The office wants the same answers from the port that the NumPy reader gives, digit for digit, so each part is checked against NumPy. It starts with the digits.

`data/digits.csv` holds {% $fig.digits %} digits, a row each: the set the digit is in, the digit its writer meant, and its {% $fig.pixels %} counts, its grid of {% $fig.side %} by {% $fig.side %} a row at a time. In `digits.py`, write:

- `load(path)`, the file's digits as three tensors: `pixels`, a row of counts for each digit, as `float64`, and `digits` and `sets`, the digit each shows and the set it's in, as `int64`.
- `images(pixels)`, each digit's counts as its grid, {% $fig.side %} rows of {% $fig.side %}, sharing the memory of `pixels`, so nothing is copied.
- `transposed(pixels)`, each digit's grid transposed, its columns read as rows, back in rows of {% $fig.pixels %}.
- `scaled(batch, train)`, the counts in `batch` scaled as the NumPy reader scaled them: less each pixel's mean over the training digits `train`, divided by its spread over them, with a spread of 0 taken as 1.

```
load(path) -> (pixels, digits, sets)
images(pixels) -> grids
transposed(pixels) -> rows
scaled(batch, train) -> the batch, scaled
```
