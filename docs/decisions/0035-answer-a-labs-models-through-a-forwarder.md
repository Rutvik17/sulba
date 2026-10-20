# 35. Answer a lab's models through a forwarder that keeps each connection open

- Status: accepted
- Date: 2026-10-20

## Context

Record 34 serves a lab's models from one llama-server in router mode, at `http://127.0.0.1:9931/v1`. Requests sent one after another through one httpx client, as the Embeddings for search lab's code sends its batches of passages, failed about one time in ten with "Server disconnected without sending a response". The router answers in chunks and says the connection stays open, then closes it. A client that sends its next request before the close reaches it gets no answer. httpx asks for every connection to stay open, so a learner's code meets this on any request, and a model's own llama-server, record 32's, does the same after each streamed reply. The server is llama.cpp's own build, pinned by sha256; the runner is Sulba's.

## Decision

- `uv run sulba.py model` starts llama-server as record 34 sets, at a free port on this computer, and answers at the lab's address itself, `http://127.0.0.1:9931/v1` or the port `--port` gives: a forwarder in `sulba.py`, on Python's `http.server`, passes each request to the server on a connection of its own, and the answer back in chunks as they come, so a streamed reply still streams. It keeps each program's connection open from one request to the next.
- Until the server listens, the forwarder answers as the server does while it loads a model: `503`, with `{"error": {"message": "Loading model", "type": "unavailable_error", "code": 503}}`.
- When the forwarder can't take the port, the runner says the port is in use, as it does when something answers there.

## Options

| Option | What it does well | Where it falls short |
| --- | --- | --- |
| A forwarder in the runner, in front of the router (chosen) | Every answer, streamed or not, on a connection the program keeps; one address with every model by its name, as record 34 has it; Python's standard library only | One more step, in Python, for every request; the runner holds a port as well as the server |
| A llama-server for each model, at a port of its own | An answer that isn't streamed keeps its connection open | A streamed reply still closes its connection; an address for each model, which record 34 set aside |
| Retries in the learner's code | No change to the runner | Every lab's code would retry a failure its own computer's server causes, and a program can't tell a request the server never read from one it ran |
| Wait for llama.cpp to change | Nothing to build | llama.cpp's master branch has the same code on 2026-10-20 |

## Evidence

- In a 4-CPU container, with llama-server b11734 in router mode serving nomic-embed-text-v1.5 as record 34 sets it, one httpx client sending requests one after another got "Server disconnected without sending a response" for 5 of 60 short requests, and for 3 of 30 longer ones. Sent straight to the model's own server, the process the router passes them to, the same requests all got answers.
- On a raw connection, with the headers httpx sends, which include `Connection: keep-alive`, the router answered the first request in chunks, with `Keep-Alive: timeout=5, max=100` and no `Connection: close`, then closed the connection without answering the second. The model's own server answered 100 requests on one connection, the last with `Connection: close`. A llama-server serving one chat model, stories260K, kept its connection open over five answers that weren't streamed, and closed it the same way after the first streamed one.
- [server-http.cpp at b11734](https://github.com/ggml-org/llama.cpp/blob/b11734/tools/server/server-http.cpp#L646-L660) writes a streamed answer through cpp-httplib's chunked content provider, which at the end calls `sink.done()` and returns `has_next`, then false. [cpp-httplib 0.61.0, as llama.cpp vendors it at b11734](https://github.com/ggml-org/llama.cpp/blob/b11734/vendor/cpp-httplib/httplib.cpp#L4256-L4258), takes a provider that returns false as cancelled, `error = Error::Canceled`, and the server closes the connection. [The router](https://github.com/ggml-org/llama.cpp/blob/b11734/tools/server/server-models.cpp#L1916) answers each request it passes to a model through such a stream. On 2026-10-20, [server-http.cpp on llama.cpp's master branch](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/server-http.cpp) has the same code.
- Through the forwarder, in front of the same router, 200 short requests and 60 longer ones from one httpx client all got answers, and three raw connections took 150 requests each, whatever `Connection` header they sent. A streamed reply from stories260K came through in 63 events, ending with `[DONE]`, and the same client's next request, for an embedding, got its answer. Over 200 short embedding requests, each sent through the forwarder and then straight to the router in turn, the forwarder added 0.4 ms and 2.1 ms to the median request, of about 50 ms, in two runs.

## Why

The forwarder keeps the address and the names record 34 gives a learner's code, and mends streamed replies as well as the rest, which a server for each model would not. It is under a hundred lines of Python's standard library in the runner, tested against a stand-in that closes its connections as the router does. The strongest case against: it is code that exists only to make up for a fault in llama.cpp, in the path of every request a learner's code sends, and it has to pass on whatever the server's API answers, a stream included.

## Consequences

Every answer reaches the learner's code through Python, which copies it chunk by chunk, at a cost of a couple of milliseconds a request. The runner takes two ports, the lab's and one the system gives the server, and stops both at Ctrl+C. Record 34 still says what serves the models, how and from where.

## Revisit when

llama.cpp's server keeps a connection open after a streamed answer, in a release the runner pins.
