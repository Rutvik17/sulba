# Shipping the desk

The lab's stages, run on your machine. Install [uv](https://docs.astral.sh/uv/), then in this folder run:

```sh
uv run sulba.py
```

It runs the tests of the stage you're on. When the stage is done, it gives you a link that marks it done on the lab's page. Start the next stage with `uv run sulba.py next`, and finish a Catch stage's review with `uv run sulba.py finish`.

The desk is the app from The chat page: `app.py` and the files it imports, served with its page by `serve.py`. `uv run sulba.py build` compiles the page's TypeScript into `static/`. Its first run downloads Node.js for your system from nodejs.org, and the page's packages from registry.npmjs.org, into `sulba` in your cache folder.

`uv run sulba.py db` starts the lab's database, Postgres, for the desk to use, until you press Ctrl+C. It prints the address to connect to, and keeps what you put in it in `.sulba/database`. On Linux, the database's first run fetches pgvector from apt.postgresql.org into `sulba` in your cache folder.

`uv run sulba.py model` starts the lab's models, Qwen3.5-4B and nomic-embed-text-v1.5, for the desk to call at `http://127.0.0.1:9931/v1`, until you press Ctrl+C. The first time, it downloads them from huggingface.co, and llama.cpp's server for your system, from github.com, into `sulba` in your cache folder.

## Running the desk

Once you've written the stages, build the page, start the database and the models, set the desk's settings, and run `main.py`:

- `DESK_DATABASE_URL`, the database's address;
- `DESK_ISSUER`, your OpenID provider's issuer, and `DESK_CLIENT_ID` and `DESK_CLIENT_SECRET`, the desk's id and secret there, with `http://127.0.0.1:8000/auth/callback` as its redirect URI;
- `DESK_PROMPT_PRICE` and `DESK_COMPLETION_PRICE`, if you want the dashboard to show what the tokens would cost at a model's prices, in dollars for a million tokens.

```sh
uv run sulba.py build
uv run main.py
```

`main.py` listens on every address of your machine, on `PORT`, 8000 if it isn't set, as a container needs. Open `http://127.0.0.1:8000` and sign in. `/health` says the desk is up, and `/ready` whether its database and model answer.

## The image

With Docker, or another builder that reads a Dockerfile, build the desk's image in this folder:

```sh
docker build --tag desk .
```

The build downloads its base images from Docker Hub and ghcr.io, and the desk's packages from registry.npmjs.org and pypi.org. Put the desk's settings in a file, one `NAME=value` a line, and keep it out of every file you share. To reach the database and the models the lab starts on your machine, run the image on your machine's network, where `127.0.0.1` is your machine as it is for `main.py`:

```sh
docker run --rm --network host --env-file desk.env desk
```

Docker Engine on Linux runs a container on the host's network as it is; Docker Desktop does from version 4.34, once Enable host networking is checked in its Network settings.

## On a host

A host that runs a Dockerfile, such as Render, builds the image from your repository and runs it with the settings you give it. The desk needs a database and models the host can reach: a Postgres service, such as Neon, at the address in `DESK_DATABASE_URL`, and the lab's two models, served by their names, at the address in `DESK_MODEL_URL`. Set the provider's redirect URI to the host's address with `/auth/callback`, and `DESK_PUBLIC_URL` to the host's address. Set the host's health check to `/health`, or to `/ready` if it should also wait for the database and the model. Check each provider's current plans and prices before you start: free plans change, and some sleep when idle.
