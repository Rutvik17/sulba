# The readmission service

Your code from the lab, with the extract it learns from. Install [uv](https://docs.astral.sh/uv/), then run these in this folder.

Train the model and save it to `model.joblib`:

```sh
uv run python train.py
```

Run your tests:

```sh
uv run pytest test_app.py
```

Start the service:

```sh
uv run uvicorn app:app
```

It answers at http://127.0.0.1:8000, and http://127.0.0.1:8000/docs describes each endpoint and sends it requests.
