The service shouldn't train each time it starts. Training needs the extract, which the server has no reason to hold, and every start would fit the model again. Train once, on a machine with the extract, save what `train` gives, and let the service load the file.

Add to `train.py`:

```
MODEL_PATH = "model.joblib"
versions() -> {"scikit-learn": ..., "numpy": ..., "scipy": ...}, the versions running
save(trained, path=MODEL_PATH) -> writes trained and versions() to path with joblib.dump
load(path=MODEL_PATH) -> trained, as save wrote it
```

scikit-learn doesn't support loading a model with versions other than the ones that saved it, so `load` raises a `ValueError` when the versions the file holds aren't `versions()`. `save` writes one object that holds both, such as a dict, and leaves `trained` as it was. Run as `python train.py`, the script trains on the lab's extract and saves to `MODEL_PATH`.
