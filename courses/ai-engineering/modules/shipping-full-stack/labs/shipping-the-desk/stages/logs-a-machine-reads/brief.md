A host keeps what the desk writes to standard output and lets you search it. A search works on lines a program can read: one JSON object a line, with the request each line came from, and none of the secrets a request or a setting holds.

In `logs.py`, write:

- `JsonFormatter`, a `logging.Formatter` whose `format(record)` gives one line of JSON: the record's `time` in UTC, to the millisecond, its `level`, `logger` and `message`, then each field the call's `extra` gave it. A record with an error has the traceback as `error`, in the same line. While the desk answers a request, the line has the request's id as `request_id`.
- `redacted(value)`, the value with what's under every key that names a secret replaced by `[hidden]`, in dictionaries and lists at any depth. A key names a secret when it has `authorization`, `cookie`, `database_url`, `password`, `secret` or `token` in it, in any case. Every line goes through it.
- `configure()`, which sends every record at `INFO` and above to standard output through the formatter, and nowhere else.
- `RequestIds`, ASGI middleware around an app. Each HTTP request gets an id: the caller's `X-Request-ID` when it's 1 to 64 letters, digits, dots, dashes or underscores, and otherwise a new random one. The answer carries the id back in `X-Request-ID`, and every line written while the request is answered has it, for requests answered at once too. Once the request is answered, the middleware logs one line, `request`, on the `desk.requests` logger, with the `method`, the `path` without its query, the `status`, 500 for a request that failed, and `ms`, the milliseconds it took.

```python
JsonFormatter().format(record: logging.LogRecord) -> str
redacted(value: Any) -> Any
configure(level: int = logging.INFO) -> None
RequestIds(app: App, logger: logging.Logger | None = None)
```

`request_id`, the context variable that holds the id, is in the starter.
