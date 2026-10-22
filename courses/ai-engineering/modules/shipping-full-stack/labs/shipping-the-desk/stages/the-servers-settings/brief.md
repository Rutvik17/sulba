On a host, the desk runs as one process, `python main.py`, which starts uvicorn with settings for where it runs: the address and port the host sends requests to, which proxies to believe about who a caller is, how long to give open requests when it's told to stop, and logs that are the desk's own.

In `main.py`, write:

- `production(app)`, the app with `/ready` from your `health.py` and your `RequestIds` around it.
- `port_from(environ)`, the port in `PORT`, 8000 when it isn't set. A value that isn't a whole number from 1 to 65535 raises `ValueError`, naming `PORT`.
- `config(environ)`, the server's settings as a `uvicorn.Config` of `main:create`, a factory:
  - every address of the machine, `0.0.0.0`, on the port `port_from` gives;
  - the caller's address from `X-Forwarded-For` only when the request comes from a proxy that `FORWARDED_ALLOW_IPS` names, or from the machine itself when it names none;
  - `SHUTDOWN_SECONDS` for open requests once the server is told to stop;
  - no logging settings of uvicorn's, so its lines go through the desk's, and no access log, since `RequestIds` logs each request with its id.

```python
production(app: FastAPI) -> FastAPI
port_from(environ: Mapping[str, str]) -> int
config(environ: Mapping[str, str]) -> uvicorn.Config
```

`create()`, which the server calls, is in the starter: it sets up the desk's logs and makes the desk with its page, from `serve.py`.
