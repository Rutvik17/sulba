In `app.py`, put the desk together with sign-in, so that `uv run uvicorn app:create_app --factory` serves it to people signed in with an OpenID provider:

- `settings_from(environ)` gives the settings, now with `DESK_ISSUER`, the provider's issuer, an `https://` address; `DESK_CLIENT_ID` and `DESK_CLIENT_SECRET`, the desk's id and secret at the provider, the secret a `SecretStr`; and `DESK_PUBLIC_URL`, the address the desk is served at, with no path, by default `http://127.0.0.1:8000`. The first three have no default.
- `settings.registration` gives the `Registration` for `desk_auth.py`: the id, the secret, the redirect URI, which is the public address followed by `/auth/callback`, and `secure`, true when the public address is `https://`.
- `create_app(settings, data, client, identity)` takes the client for the provider as `identity`, or makes one and closes it as it stops. As the app starts, it applies the desk's migrations, the sessions' and `OWNERS`, then discovers the provider, and keeps `Sessions`, the registration, the provider and its `Keys` in `app.state`. It includes the sign-in routes, and `GET /me` gives the person signed in.
- `GET /usage` counts the turns of the person's own conversations.
- A request whose method isn't GET, HEAD or OPTIONS is refused with 403 when the browser says it comes from another site: when its `Sec-Fetch-Site` header is anything but `same-origin` or, without that header, when it has an `Origin` that isn't the public address.

What the app must do:

- refuse settings without the provider's, or with an issuer that isn't HTTPS or a public address with a path, naming the variable, and show the secret nowhere;
- send its cookies only over HTTPS when it's served over HTTPS;
- take no change from another site;
- give each person their own conversations and usage alone;
- not start when its provider can't be found.

How it does so is yours to choose.

```
settings_from(environ) -> Settings
create_app(settings=None, data=Path("data"), client=None, identity=None) -> FastAPI
GET /me
GET /usage?days=7
```

Four tests run on every attempt. Then five checks run before the code ships.

Registered with a provider, and with the database and the models running, the app serves the desk to people signed in there. The project's `README.md` says how.
