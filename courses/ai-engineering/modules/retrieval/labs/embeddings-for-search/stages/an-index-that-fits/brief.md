The help desk's search will keep its index in memory on a small server, with room for {% $fig.budget %} bytes a passage, ids included. This stage builds the index it will ship, in `index.py`, with your `Cache`, `shorten`, `quantize` and `restore`:

- `Index.build(client, cache, passages)` embeds the passages, a dictionary of texts by id, through the cache, and keeps their vectors in the index.
- `index.find(client, cache, questions, k)` gives the ids of each question's `k` best passages, best first, and of two that tie, the one that comes first in `passages`.
- `index.save(path)` writes the index to one file, and `Index.load(path)` reads it back.

How the index keeps each vector is yours to choose: how many of its numbers, and in how many bytes each. Shorter vectors measured what each choice costs on the validation questions. The checks use the {% $fig.test %} test questions, with the vectors nomic-embed-text-v1.5 gave them and the passages: the index's hit rate at {% $fig.k %} must be at least {% $fig.kept %}% of the full vectors' {% $fig.full %}.

```
Index.build(client, cache, passages) -> Index
index.find(client, cache, questions, k=5) -> list of lists of ids
index.save(path)
Index.load(path) -> Index
```

Two tests run on every attempt. Then five checks run before the code ships.
