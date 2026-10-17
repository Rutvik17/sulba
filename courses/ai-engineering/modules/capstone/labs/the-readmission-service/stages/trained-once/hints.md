`joblib.dump(value, path)` writes a Python value to path, and `joblib.load(path)` gives it back. Save `{"trained": trained, "versions": versions()}`.

---

Each package keeps its version in `__version__`, such as `sklearn.__version__`.

---

In `load`, compare the versions the file holds with `versions()`, and raise the `ValueError` before returning anything.
