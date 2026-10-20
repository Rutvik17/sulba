Each vector holds {% $fig.numbers %} float32 numbers, {% $fig.bytes_full %} bytes, so the help desk's {% $fig.passages %} passages take {% $fig.megabytes %} MB, and a million passages would take {% $fig.gigabytes %} GB. A vector can be smaller two ways. nomic-embed-text-v1.5 was trained to work cut short, by Matryoshka representation learning: its card shortens a vector by layer normalization, which takes the mean of its numbers away and divides them by their standard deviation, then keeps the first numbers and scales them to a length of 1. And each number can take one byte instead of four, as one of 256 steps between the lowest and the highest that number takes across the passages.

In `shorten.py`, write:

- `shorten(vectors, numbers)`: each row cut to its first `numbers` as the card cuts it, as float32. PyTorch's `layer_norm`, which the card calls, divides by `sqrt(variance + 1e-5)`, the variance being the mean of the squared differences from the mean.
- `bounds(vectors)`: the lowest and the highest value of each column.
- `quantize(vectors, low, high)`: each number as the nearest of 256 steps from its low, 0, to its high, 255, as uint8. A number below its low or above its high takes the nearest end, and one whose low and high are equal takes 0.
- `restore(codes, low, high)`: the numbers the codes stand for, `low + code * (high - low) / 255`, as float32.

On the {% $fig.questions %} validation questions, each cut as the passages are and searched against every passage:

| Each passage | Bytes | Recall at 5 |
| --- | --- | --- |
| All {% $fig.numbers %} numbers | {% $fig.bytes_full %} | {% $fig.recall_full %} |
| The first 256 | {% $fig.bytes_256 %} | {% $fig.recall_256 %} |
| The first 128 | {% $fig.bytes_128 %} | {% $fig.recall_128 %} |
| The first 64 | {% $fig.bytes_64 %} | {% $fig.recall_64 %} |
| The first 256, a byte each | {% $fig.bytes_bytes %} | {% $fig.recall_bytes %} |

Recall at 5 is the share of questions with a passage that answers them among the first five found.

```
shorten(vectors, numbers) -> np.ndarray
bounds(vectors) -> (low, high)
quantize(vectors, low, high) -> np.ndarray of uint8
restore(codes, low, high) -> np.ndarray
```
