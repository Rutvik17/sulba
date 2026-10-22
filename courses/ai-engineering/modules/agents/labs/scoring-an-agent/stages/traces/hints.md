The client's `base_url` is an `httpx.URL`, with its `host`, its `scheme` and its `port`, which is `None` when the URL gives none.

---

`tracer.start_as_current_span(name, kind=..., attributes=...)` is a context manager that makes the span current while it lasts, so that spans started inside it are its children. An exception that leaves it is recorded on the span and sets its status to `ERROR`, so catch it only to set `error.type`, and raise it again.

---

A finished span's `context.trace_id` names its trace, its `parent` is `None` when it's a root, its `start_time` and `end_time` are nanoseconds, and its `attributes` are a mapping.
