A key holds everything its vector comes from. Keyed by the text alone, the cache would hand a question the vector of a passage with the same words, and keep handing out the old model's vectors after the help desk moved to a new one. sha256 gives every text a key of the same 64 digits, however long the text, and two texts with the same key are too unlikely to plan for.

`with connection:` commits its block's rows as one transaction, and SQLite's transactions are atomic and durable "even if the transaction is interrupted by a program crash, an operating system crash, or a power failure", in its documentation's words. So a run cut short, by a failed request or by Ctrl+C, keeps every batch before it. Committing each batch costs a write to the disk, far less time than the model takes to embed the batch.

A text's vector can also differ a little from one request to another: llama.cpp's server works out a request's texts together, and the texts beside one change its numbers slightly. The cache keeps the first vector it gets, so every later search uses that one.

A cache only works if a text is the same each time. The cache treats "Bring proof of your age." and "Bring proof of your age. " as two texts, so the help desk keeps each passage's text exactly as it embeds it.

With the lab's model running, a second run of the same texts makes no requests:

```python
from pathlib import Path

import httpx

from cache import Cache
from embed import DOCUMENT

passages = ["You can apply for disability benefits online.", "Bring proof of your age."]
with httpx.Client(base_url="http://127.0.0.1:9931/v1", timeout=60) as client:
    with Cache(Path("vectors.sqlite")) as cache:
        print(cache.vectors(client, passages, DOCUMENT).shape)
        print(cache.vectors(client, passages, DOCUMENT).shape)
```
