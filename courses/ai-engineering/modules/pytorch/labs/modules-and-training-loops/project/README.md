# Modules and training loops

The lab's stages, run on your machine. Install [uv](https://docs.astral.sh/uv/), then in this folder run:

```sh
uv run sulba.py
```

It runs the tests of the stage you're on. When the stage is done, it gives you a link that marks it done on the lab's page. Start the next stage with `uv run sulba.py next`, and finish a Catch stage's review with `uv run sulba.py finish`.

The first run downloads PyTorch, which is up to 200 MB, from PyTorch's own index.
