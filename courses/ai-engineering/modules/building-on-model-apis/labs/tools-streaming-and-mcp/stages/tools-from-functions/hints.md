`inspect.signature(function).parameters` gives the parameters in order, and `typing.get_type_hints(function, include_extras=True)` their types, `Annotated` kept.

---

`typing.get_origin` and `typing.get_args` take a type apart: `Literal`, `list`, `Annotated`, and for `str | None`, `types.UnionType`, with `type(None)` among its arguments.

---

In `run`, each way a call can fail becomes its own `{"error": ...}`: a `KeyError` for the name, a `json.JSONDecodeError` for the arguments, a set of keys that isn't the function's parameters, and any `Exception` the function raises.
