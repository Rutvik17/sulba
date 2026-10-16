Each day's export arrives as a file named for its day, such as `2026-10-16.jsonl`, and the service checks it before the day's records go on to screening. Write:

```
check_export(path, struct) -> the records of the export at path, or raises an
    ExceptionGroup of every line that fails, noted with the export's name
```

with this note on the group:

```
Export 2026-10-16.jsonl
```

`path` is a `pathlib.Path`, and `path.name` is its file's name. `open(path, encoding="utf-8")` opens a file as text in UTF-8, where the default encoding depends on the machine. A file gives its lines one at a time, and is a context manager of its own, whose `__exit__` closes it. One `with` statement can hold several context managers, separated by commas, as if each were inside the one before it, so they're left in the reverse order. Hidden tests check what `check_export` gives, and three checks test it before it ships.
