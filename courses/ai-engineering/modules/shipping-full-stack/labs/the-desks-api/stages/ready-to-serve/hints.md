`FastAPI(lifespan=lifespan)` runs `lifespan`, an async context manager made with `@asynccontextmanager`, around the app's life: the code before its `yield` as the app starts, and the code after it as the app stops.

---

`Settings(**values)` raises `ValidationError`, whose `errors()` gives each error's `loc`, starting with the field's name. Turn it into a `ValueError` that names each field's variable.
