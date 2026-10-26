The take-home searched the office's pages by their words, in memory. The office's assistant will search them in Postgres on the office's own server, by meaning too, with the vectors nomic-embed-text-v1.5 gives each passage there. The office edits its pages every week, so the index has to keep up with them without embedding every passage again.

`data/passages.csv` holds the office's {% $fig.passages %} passages, from its {% $fig.pages %} pages, each with its `passage`, its `page`, the page's `title` and its `text`. `uv run sulba.py db` starts the lab's database on your machine. Each test gets a new, empty one, and a scripted model server, whose `client` posts to the model's API.

In `index.py`, write:

- `read(path)`: the passages in the file at `path`, in order, each a `Passage` of its id, page, title and text.
- `connect(url)`: a connection to the database at `url` through psycopg, in autocommit mode, with `register_vector(conn)` from the `pgvector` package called on it.
- `create(conn)`: the table `passages`, with each passage's `id`, its primary key, its `page`, `title`, `body` and `digest`, all `text`, and its vector in `embedding`, a `vector(768)`, none of them null; and `words`, a `tsvector` generated from the title and the body by `to_tsvector('english', title || ' ' || body)` and stored. Index `embedding` with HNSW for cosine distance, `vector_cosine_ops`, and `words` with GIN.
- `sync(conn, client, passages)`: the table made to hold the passages given and no others. It adds a passage the table lacks, removes one that isn't given, and gives a passage whose text has changed its new text and vector. A passage whose page or title alone has changed takes them without being embedded again. It gives the ids of the passages it embedded, in the order given.

`sync` embeds texts with a POST to `client`'s `/embeddings`, whose body names `EMBEDDER` as its `model` and gives at most `BATCH` texts as its `input`, each after `DOCUMENT`. What `digest` keeps is yours to choose, so long as `sync` can tell from it which texts have changed. When a request fails, `sync` raises its error and leaves the table as it was.

```
read(path) -> list of Passage
connect(url) -> psycopg.Connection
create(conn)
sync(conn, client, passages) -> list of ids
```
