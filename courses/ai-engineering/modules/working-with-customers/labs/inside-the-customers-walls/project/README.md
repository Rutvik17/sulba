# Inside the customer's walls

The lab's stages, run on your machine. Install [uv](https://docs.astral.sh/uv/), then in this folder run:

```sh
uv run sulba.py
```

It runs the tests of the stage you're on. When the stage is done, it gives you a link that marks it done on the lab's page. Start the next stage with `uv run sulba.py next`, and finish a Catch stage's review with `uv run sulba.py finish`.

`sign_in.py` and `tokens.py` are Signing in's, for your code to use: `discover` reads an OpenID provider's addresses, and `Keys` fetches its signing keys.
