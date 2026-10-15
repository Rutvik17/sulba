The clinic's system will find records through a class, and not only among these standardized measurements: the other tables it keeps aren't standardized, and some hold measurements far from 0 compared with the differences between them. A sample can also be sent twice, and the clinic spots one by its distance of exactly 0 to a record.

Ship `Nearest`. It's made from records as they are, standardized or not. Its `find` gives each new sample's `k` nearest records, nearest first, and their distances, worked out from the dot products with no more than {% $fig.budget_mb %} MB of arrays at once. Moving every sample by the same amount changes no distance, and a sample less its copy is exactly 0.

```
Nearest(records) -> the search over these records
nearest.find(new, k=5) -> (near, distances)
```

The checks measure memory with Python's `tracemalloc`, which counts the memory of every array NumPy makes.

There are no hints. The tests are hidden: you see which pass, but not their inputs. Four more checks decide whether it ships.
