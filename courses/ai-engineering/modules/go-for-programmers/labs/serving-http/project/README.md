# Serving HTTP

The lab's stages, run on your machine. Install [uv](https://docs.astral.sh/uv/), then in this folder run:

```sh
uv run sulba.py
```

It runs the tests of the stage you're on. When the stage is done, it gives you a link that marks it done on the lab's page. Start the next stage with `uv run sulba.py next`, and finish a Catch stage's review with `uv run sulba.py finish`.

The stages are Go, in the module `example/gateway` that `go.mod` names. `request.go`, `routes.go`, `fallback.go` and `failures.go` are the gateway's request, routes, upstreams and error replies, from Types, errors and interfaces, and `bucket.go` is its rate limit, from Goroutines, channels and context. The first run downloads Go for your system from dl.google.com into `sulba` in your cache folder.
