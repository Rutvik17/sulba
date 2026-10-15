The clinic's records will grow to {% $fig.big_records %}, and its system will look up new samples {% $fig.lookups %} at a time. `search` builds every difference at once, an array of shape ({% $fig.lookups %}, {% $fig.big_records %}, {% $fig.measurements %}): {% $fig.full_mb %} MB, and as much again when it squares them. The system can give the search {% $fig.budget_mb %} MB.

Ship `Search`. It standardizes its records once, when it's made, with their own mean and standard deviation. Its `find` gives what `search` gives, each new sample's `k` nearest records, nearest first, their distances and the share of them that are malignant, but never holds more than `BUDGET` bytes of arrays at once. Work through the new samples a few rows at a time.

```
Search(records, diagnoses) -> the search, its records standardized
search.find(new, k=5) -> (near, distances, share)
```

The checks measure memory with Python's `tracemalloc`, which counts the memory of every array NumPy makes.

If you missed any of stage 4's problems, this stage starts from the fixed `search.py`. There are no hints. The tests are hidden: you see which pass, but not their inputs. Four more checks decide whether it ships.
