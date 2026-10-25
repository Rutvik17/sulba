# Signing in

The lab's stages, run on your machine. Install [uv](https://docs.astral.sh/uv/), then in this folder run:

```sh
uv run sulba.py
```

It runs the tests of the stage you're on. When the stage is done, it gives you a link that marks it done on the lab's page. Start the next stage with `uv run sulba.py next`, and finish a Catch stage's review with `uv run sulba.py finish`.

`uv run sulba.py db` starts the lab's database, Postgres, for your code to use, until you press Ctrl+C. It prints the address to connect to, and keeps what you put in it in `.sulba/database`. On Linux, the database's first run, or the first test that uses it, fetches pgvector from apt.postgresql.org into `sulba` in your cache folder.

`uv run sulba.py model` starts the lab's models, Qwen3.5-4B and nomic-embed-text-v1.5, for your code to call by those names at `http://127.0.0.1:9931/v1`, until you press Ctrl+C. The first time, it downloads them from huggingface.co, and llama.cpp's server for your system, from github.com, into `sulba` in your cache folder.

To sign people in, register the desk as a web application with an OpenID provider, with `http://127.0.0.1:8000/auth/callback` as its redirect URI. With Google, that's an OAuth client of the Web application type, made on the Clients page of the Google Cloud console, whose issuer is `https://accounts.google.com`. Keep the client's secret out of every file you share.

Once you've written `app.py`, start the database and the models, set these environment variables, and serve the desk:

- `DESK_DATABASE_URL`, the database's address;
- `DESK_ISSUER`, the provider's issuer;
- `DESK_CLIENT_ID` and `DESK_CLIENT_SECRET`, the desk's id and secret there.

```sh
uv run uvicorn app:create_app --factory
```

It answers at `http://127.0.0.1:8000`, with its interactive documentation at `http://127.0.0.1:8000/docs`. Open `http://127.0.0.1:8000/auth/sign-in` to sign in.
