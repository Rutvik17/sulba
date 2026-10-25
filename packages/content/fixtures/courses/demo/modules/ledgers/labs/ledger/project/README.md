# Ledger

The lab's stages, run on your machine. Install [uv](https://docs.astral.sh/uv/), then in this folder run:

```sh
uv run sulba.py
```

It runs the tests of the stage you're on. The first time, it also downloads the files the lab needs into `data`. When the stage is done, it gives you a link that marks it done on the lab's page. Start the next stage with `uv run sulba.py next`, and finish a Catch stage's review with `uv run sulba.py finish`.

`uv run sulba.py model` starts the lab's models, stories260K, bge-small-en-v1.5 and jina-reranker-v1-tiny-en, for your code to call each by its name at `http://127.0.0.1:9931/v1`, until you press Ctrl+C. The first time, it downloads the models from huggingface.co, and llama.cpp's server for your system, from github.com, into `sulba` in your cache folder.

`uv run sulba.py db` starts the lab's database, Postgres with pgvector, for your code to use, until you press Ctrl+C. It prints the address to connect to, and keeps what you put in it in `.sulba/database`. On Linux, the database's first run, or the first test that uses it, fetches pgvector from apt.postgresql.org into `sulba` in your cache folder.

The lab's Spark tests run on Sail, which starts inside the run, so they need nothing else installed.

The lab's TypeScript stage runs in Node.js. Its first run downloads Node.js for your system from nodejs.org, and the lab's packages from registry.npmjs.org, into `sulba` in your cache folder.

`uv run sulba.py build` compiles `statement.ts` into `static/statement.js`, for a browser to load.
