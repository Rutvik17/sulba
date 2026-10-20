Matryoshka representation learning trains a model's vectors coarse to fine, so that their first numbers make a smaller vector of their own, as the dolls of the name sit inside each other.

The card's layer normalization takes the mean away and divides by the standard deviation, and the last step scales the vector to a length of 1. Dividing by any positive number before that changes nothing it ends with, so the standard deviation drops out, and the cut comes to the mean taken away, the first numbers kept, and a length of 1. Without the last step, a vector cut short is shorter than 1, by more for some passages than for others, and the search favours the longest.

A byte for each number keeps 256 steps between that number's low and high, so the bounds come from the passages the index holds. A passage added later can fall past them, which is why `quantize` clips: cast with `astype(np.uint8)` alone, a value past 255 has no defined result, which NumPy's release notes say "may return an undefined result", and machines differ. The questions keep their float32 numbers and meet the restored passages, so only the passages lose anything to the steps.

The table measures each choice the way the help desk will use it, on its own passages and questions. On another set of texts, the same choices can cost more or less.
