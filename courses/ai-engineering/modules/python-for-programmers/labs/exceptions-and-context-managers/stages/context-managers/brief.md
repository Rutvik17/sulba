Some of the service's code checks lines as they come from more than one place, so it can't hand `check_day` a day's lines at once. A context manager gives such code a batch to check lines into one at a time, and raises their errors together when the code is done. Write:

```
noted(note) -> a context manager that adds note to any error raised in its block, and
    lets the error go on
Batch(struct) -> a context manager whose check(line, number) keeps each line's record
    in records, or its error in errors, and that raises the errors together, in an
    ExceptionGroup, when its block ends
```

`with manager as value:` calls `manager.__enter__()` and gives the block what it returns. However the block ends, it then calls `manager.__exit__(kind, error, traceback)`: with the error's class, the error and its traceback when the block raised one, and three `None`s when it didn't. When `__exit__` returns a true value, the error is suppressed. JavaScript's `using` declaration calls an object's `[Symbol.dispose]()` as its block ends, much as `with` calls `__exit__`, but `__exit__` is also given the block's error, and can suppress it.

`@contextmanager` makes a context manager from a generator function that yields once: the code before the `yield` runs as the block begins, an error raised in the block is raised again at the `yield`, and the code after it runs as the block ends. Import it at the top of `errors.py`, with `from contextlib import contextmanager`, and put it above `noted`.

A batch whose block raises an error of its own lets that error go on, as it was, without the group. The group's message counts every line the batch checked, as `check_day`'s does.
