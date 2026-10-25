# Analytical SQL

The lab's stages, run on your machine. Install [uv](https://docs.astral.sh/uv/), then in this folder run:

```sh
uv run sulba.py
```

It runs the tests of the stage you're on. The first time, it also downloads the files the lab needs into `data`: August 2025's yellow cab trips and the taxi zones, from d37ci6vzurychx.cloudfront.net, where the Taxi and Limousine Commission publishes them. When the stage is done, it gives you a link that marks it done on the lab's page. Start the next stage with `uv run sulba.py next`, and finish a Catch stage's review with `uv run sulba.py finish`.

`uv run sulba.py db` starts the lab's database, Postgres, for your own queries, until you press Ctrl+C. It prints the address to connect to, and keeps what you put in it in `.sulba/database`. `trips.py` loads it: `load(connect(url), [date(2025, 8, 5)])` creates the tables and loads the trips picked up on 5 August 2025. On Linux, the database's first run, or the first test that uses it, fetches pgvector from apt.postgresql.org into `sulba` in your cache folder.
