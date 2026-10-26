An `httpx.AsyncClient(transport=Walled(...))` sends every request through `handle_async_request`, redirects too, so the check there sees each host.

---

`request.url.host` is the host as httpx parsed it, after any user name and without the port. Compare it, lowered, with a set of the allowed names, lowered.
