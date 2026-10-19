Read a message in order: whether it's JSON, whether it's an object, then its `id`, `jsonrpc`, `method` and `params`. Keep the `id` for the reply once you know it's a string or an integer, and remember that Python counts `True` as an `int`.

---

An exception that carries a JSON-RPC error's `code`, `message` and `data` lets each check raise its error where it finds it, and `handle` turn it into the reply.

---

`Draft202012Validator(schema).iter_errors(arguments)`, from `jsonschema`, gives every way the arguments fail the tool's input schema. Check them before calling the tool, and catch what the tool raises.
