# Testing a pipeline

The lab's stages, run on your machine. Install [uv](https://docs.astral.sh/uv/), then in this folder run:

```sh
uv run sulba.py
```

It runs the tests of the stage you're on. The first time, it also downloads the files the lab needs into `data`: August 2025's yellow and green cab trips and the taxi zones, from d37ci6vzurychx.cloudfront.net, where the Taxi and Limousine Commission publishes them. When the stage is done, it gives you a link that marks it done on the lab's page. Start the next stage with `uv run sulba.py next`, and finish a Catch stage's review with `uv run sulba.py finish`.

The lab's Spark tests run on Sail, which starts inside the run, so they need nothing else installed. Run your own tests, in `test_pipeline.py`, with:

```sh
uv run pytest test_pipeline.py
```
