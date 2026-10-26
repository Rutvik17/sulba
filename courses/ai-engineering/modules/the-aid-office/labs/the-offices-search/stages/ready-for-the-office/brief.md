The office's assistant calls one function for each student's question, on the office's server, with the model on the same machine. Write it in `office.py`:

- `find(conn, client, question)`: the office's pages that best answer the question, best first, each with its best passage, as your `search` gives them; none, an empty list, when no passage is close enough to answer it; and the pages by its words alone when the model can't give the question's vector.

`find` embeds the question once, with a POST to `client`'s `/embeddings`, whose body names `EMBEDDER` and gives the question after `QUERY`, as nomic-embed-text-v1.5 takes a query. The client the office's assistant passes has no timeout of its own, and the model may answer with an error, drop the connection, or not answer at all.

How close is close enough, and how much meaning weighs against words, are yours to choose. The checks use the test questions, the office's {% $fig.test %} and the other services' {% $fig.others_test %}: at least {% $fig.found %} of the office's must have their page among the pages `find` gives, and at least {% $fig.declined %} of the others' must get none.

```
find(conn, client, question) -> list of (page, id)
```

Two tests run on every attempt. Then five checks run before the code ships.
