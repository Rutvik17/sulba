The service ships to the clinic as a container, and the clinic approves each package it runs, at the versions it has reviewed. Its approved list gives each package's name and the versions approved, as a version specifier:

```python
approved = {
    "numpy": ">=2.4,<2.5",
    "pandas": "~=3.0.0",
    "PyYAML": "==6.0.*",
}
```

A project's `pyproject.toml` lists the packages it needs, each with the versions it works with, as `package.json` does for npm. `uv lock` picks a version of each, and of each package those need in turn, and writes them all to `uv.lock`, as npm writes `package-lock.json`. `uv sync` installs the versions the lock file holds, and `uv run` locks and syncs the project before it runs a command. Write:

```
unapproved(lock: str, approved: dict[str, str]) -> list[str]
```

which reads the text of a `uv.lock` and gives a message for each package in it that the list doesn't approve, in the lock file's order:

```
tzdata 2025.3 isn't on the approved list
numpy 2.5.3 is outside the approved >=2.4,<2.5
```

A lock file is TOML. `tomllib.loads` reads it into a dict, where each `[[package]]` table is a dict, in a list under `"package"`, with the package's `name`, `version` and `source`. The lock file lists the service too, with the source `{ editable = "." }`, and the service needs no approval. `uv.lock` holds the packages for every platform and Python version the project supports, so it can list a package more than once, at different versions for different platforms or Python versions.

`"2.4.6" in SpecifierSet(">=2.4,<2.5")` is `True`: a `SpecifierSet` holds the versions a specifier allows. `canonicalize_name` gives a name as Python's packaging standards compare it: lowercase, with each run of `-`, `_` and `.` made one `-`. `approvals.py` joins the service, so it passes `mypy --strict` too. Hidden tests check what `unapproved` gives, and three checks test it before it ships.
