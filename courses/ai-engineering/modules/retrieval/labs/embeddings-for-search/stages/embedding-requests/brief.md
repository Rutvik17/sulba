A help desk answers people's questions about four US public services: Social Security, veterans' benefits, federal student aid and New York State's DMV. It wants an assistant that finds, on the services' help pages, the passages that answer each question, and this lab builds that search. The pages are copies from the MultiDoc2Dial dataset, so some of what they say, such as amounts and dates, may have changed since. The search starts with an embedding model, which turns a text into a vector, a list of numbers, so that texts about the same thing get vectors that point the same way. The lab's model is nomic-embed-text-v1.5. `uv run sulba.py model` serves it on your machine, at `http://127.0.0.1:9931/v1`, with the embeddings API that OpenAI's API defines and llama.cpp's server serves too.

In `embed.py`, write `embed(client, texts, prefix, batch)`. `client` is an `httpx.Client` whose base URL is the API's. Post to `/embeddings` a JSON body with:

- `model`: `MODEL`;
- `input`: a list of texts, each with `prefix` before it.

nomic-embed-text-v1.5's model card says that each text must start with what it's for: `search_document: ` for a passage to search, and `search_query: ` for a question. They're `DOCUMENT` and `QUERY`.

The reply gives each text's vector beside the place of its text in `input`:

```json
{
  "data": [
    {"embedding": [0.0213, -0.0472, ...], "index": 0, "object": "embedding"},
    ...
  ],
  "usage": {"prompt_tokens": ..., "total_tokens": ...}
}
```

Return the vectors as the rows of a float32 NumPy array, in the order of `texts`. With no texts, make no request and return an empty array, of shape `(0, 0)`.

A request can carry many texts, but a text the server can't embed fails the whole request, so send at most `batch` texts in each. The help desk's {% $fig.passages %} passages take {% $fig.requests %} requests of up to {% $fig.batch %}.

When the API answers with an error status, raise `ModelError` with the status and the error's message, which `error_message` reads from the response.

```
embed(client, texts, prefix, batch=BATCH) -> np.ndarray
```
