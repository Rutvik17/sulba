A sign-in spans two requests, the one that sends the browser to the provider and the one that brings it back, and a person stays signed in across many more. In `sessions.py`, keep both in Postgres, so that any copy of the app can finish a sign-in and find a session:

- `SESSION_MIGRATIONS` holds versions 4, 5 and 6, after the desk's own: `people`, with an id, the issuer and subject that name each person, unique together, and their email and name; `sign_ins`, each with its id, state, nonce, verifier, the path to send the person back to, and when it started; and `sessions`, each with its id, its person, when it started and when it ends.
- A browser holds only a token, 32 random bytes from `secrets.token_urlsafe(32)`, and the database keeps `hashed(token)`, the token's SHA-256 in hex, as the row's id.
- `begin(pending, back)` keeps a sign-in and gives its token. `take(token)` gives the sign-in and its path back once, deleting it as it does, or None when there's none, or it started more than `SIGN_IN_MINUTES` ago.
- `open(person)` keeps the person under their issuer and subject, bringing their email and name up to date, and gives a new session's token. A session ends `SESSION_DAYS` after it opens, however much it's used. `find(token)` gives the session's `Account`, or None when there's no such session or it has ended. `close(token)` ends it.
- `signed_in(request)` is a FastAPI dependency: the `Account` of the session whose token is in the request's `desk_session` cookie, from `request.app.state.sessions`, or a 403 when there's none.

```
Sessions(pool)
sessions.begin(pending, back) -> str
sessions.take(token) -> tuple[Pending, str] | None
sessions.open(person) -> str
sessions.find(token) -> Account | None
sessions.close(token) -> None
signed_in(request) -> Account
```

Each test gets a new database with the desk's migrations applied, and yours after them.
