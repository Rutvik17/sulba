```python
def check_export(path, struct):
    with (
        noted(f"Export {path.name}"),
        open(path, encoding="utf-8") as lines,
        Batch(struct) as batch,
    ):
        for number, line in enumerate(lines, 1):
            batch.check(line, number)
    return batch.records
```

The context managers are left from the last to the first. The batch raises its group as the block ends, the file closes with the group on its way out, and `noted` adds the export's name to the group last. An error a broken struct raises skips the batch's group and passes through the same way, so the file is closed whatever ends the block, and the caller gets the error itself.

A file opened outside a `with` statement stays open until something closes it. `lines.close()` after the loop would run only when nothing was raised, and the export that fails, the one the service most needs to deal with, would be the one left open.
