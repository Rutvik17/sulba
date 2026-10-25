`secrets.token_urlsafe(16)` gives a random id made from 16 random bytes. `HTTPStatus(404).phrase`, from `http`, gives `Not Found`.

---

FastAPI's `HTTPException` is a subclass of Starlette's, and the 404 and 405 the app gives for addresses and methods it doesn't have are Starlette's. A handler that `app.add_exception_handler` adds for `starlette.exceptions.HTTPException` takes both kinds. A handler for `RequestValidationError` takes a body that doesn't fit.

---

`error.errors()` lists each validation error with its `msg` and its `loc`. The first part of `loc` says where the error is, such as `"body"`, and the rest is the path to the field inside it. `ConfigDict(extra="forbid")` as a model's `model_config` refuses fields it doesn't have.
