```python
@contextmanager
def noted(note):
    try:
        yield
    except BaseException as error:
        error.add_note(note)
        raise


class Batch:
    def __enter__(self):
        return self

    def __exit__(self, kind, error, traceback):
        if error is None and self.errors:
            count = len(self.records) + len(self.errors)
            raise ExceptionGroup(
                f"{len(self.errors)} of {count} lines failed", self.errors
            )
        return False
```

`noted` handles every error, even `KeyboardInterrupt`, which `Exception` doesn't cover, since it only adds a note and raises the error again: a handler that stops an error going on should name the classes it means. A generator context manager that handles the block's error and doesn't raise it again suppresses it, as an `__exit__` that returns `True` does.

`__exit__` raises the group only when the block ended on its own. When the block raised an error, that error says more about what went wrong than the lines the batch kept, and returning `False` lets it go on unchanged. `with` calls `__exit__` however the block ends, so the code that holds a resource releases it there, as a file's `__exit__` closes the file.
