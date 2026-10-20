A question and the passage that answers it are different kinds of text: one asks, the other tells. nomic-embed-text-v1.5's card says that the prefix instructs the model "which task is being performed", and that a text must have one. The same model has two more, `clustering: ` and `classification: `, for texts grouped or classified rather than searched. Other embedding models ask for prefixes or instructions of their own, so they come from each model's card. The lab's Catch stage shows what a wrong one costs.

The server works out each vector in 32-bit floats, `float` in its source, so a float32 array keeps every digit it sends, in half the memory of NumPy's default, float64. It also gives each vector a length of 1, which the next stages use.

An error fails every text in its request: llama.cpp's server answers a text longer than it can take, more than {% $fig.limit %} tokens as the lab runs it, with a `500` and "input (... tokens) is too large to process". Batches keep a failure to the texts beside it, and keep each request and its reply a size the server and the client handle without trouble.

With the lab's model running, from `uv run sulba.py model` in another terminal, your code can call it:

```python
import httpx

from embed import DOCUMENT, embed

with httpx.Client(base_url="http://127.0.0.1:9931/v1", timeout=60) as client:
    vectors = embed(client, ["You can apply for disability benefits online."], DOCUMENT)
    print(vectors.shape, vectors.dtype)
```

The tests call a scripted model instead, so they give the same result on every computer, with no model running.
