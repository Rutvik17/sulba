```python
def assign(*schemas):
    return {key: field for schema in schemas for key, field in schema.items()}


def explain(path, message):
    if not path:
        return message
    shown = ".".join(str(key) for key in path)
    return f"At path: {shown} -- {message}"
```

A comprehension builds a new dict each time, so the schemas it reads stay as they were. When a key comes a second time, the dict keeps it where it first went in, with the later value, as `Object.assign` does in JavaScript.

`str(key) for key in path`, with no brackets of its own, is a generator expression: it makes each string when it's asked for the next one, and `join` asks for them all. An empty tuple is falsy, so `not path` holds for a failure at the top of a value.
