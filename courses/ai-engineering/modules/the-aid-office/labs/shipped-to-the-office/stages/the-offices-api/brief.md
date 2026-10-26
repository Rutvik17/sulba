The office's chat page sends each question to the desk's API on the office's server, which signs students in with the college's own OpenID provider. The lab gives you the sign-in as the help desk's had it: `sign_in.py`, `tokens.py`, `sessions.py`, whose tables `SESSION_MIGRATIONS` holds for `migrate` in `migrations.py`, and `desk_auth.py`, whose `router` serves `/auth/sign-in`, `/auth/callback` and `/auth/sign-out`. It also gives you `setup.py`, which sets up the office's database: the passages, the records, the tickets, and `directory`, each student's college `email` and `student` id. Each test sets the database up, and the college's provider signs its people in.

In `app.py`, write:

- `Settings`: where the model answers, `model_url`, starting `http://` or `https://`; the database, `database_url`, starting `postgresql://` or `postgres://`; the provider, `issuer`, starting `https://`; the desk's `client_id` and `client_secret` there, neither empty, the secret a `SecretStr`; and `public_url`, the address the desk is served at, with no path.
- `settings_from(environ)`: the settings from the variables in `VARIABLES`, each with its default when it isn't set, or a `ValueError` that names each variable missing or wrong.
- `create_app(settings=None, client=None, identity=None)`: the desk, with the settings given or the environment's, `client` to the model and `identity` to the provider, or ones it makes and closes as it stops.

As it starts, the app opens a `psycopg_pool.ConnectionPool` to the database, in autocommit mode, with pgvector's `register_vector` for each connection; migrates the sessions' tables; finds the provider with `discover`; and keeps what `desk_auth.py` uses on `app.state`: `sessions`, `registration`, `provider` and `keys`. It serves `desk_auth.py`'s `router`, `GET /health` and `POST /questions`.

`POST /questions` takes a question's `text`, from 1 to 1,000 characters, not all spaces, and what it's `about`, `"pages"` unless it's `"my aid"`. It answers with server-sent events: a `piece` event, `{"text": ...}`, for each piece your `stream` gives, then a `verdict` event, `{"text": ..., "pages": [...], "to_staff": ...}`. A question about the student's aid is one verdict: the record's lines, `SIGN_IN` for a visitor, or `NO_RECORD`, as `desk.py`'s `respond` gives them, without the model. A verdict to staff writes a ticket for a student signed in, and a visitor gets `STAFF_SIGNED_OUT` and no ticket.

The student is the one whose email `directory` lists for the person signed in, by their session's cookie; someone signed in that `directory` doesn't list is refused with a 403 and `NOT_A_STUDENT`. Refuse a request from another site that would change anything, as the help desk did: its browser says so in `Sec-Fetch-Site` or, without it, in `Origin`.

```
settings_from(environ) -> Settings
create_app(settings=None, client=None, identity=None) -> FastAPI
POST /questions -> piece events, then a verdict event
```
