The provider sends the browser back to the desk's redirect URI with an answer in its query: a code and the request's state, or an error. In `tokens.py`, turn that answer into the person it signed in:

- `Keys(client, provider)` holds the provider's signing keys. `await keys.key(kid)` gives the key with that id, from the provider's JWK Set at its `jwks_uri`, read with `jwt.PyJWKSet.from_dict`. The keys are fetched the first time one is needed, and again only when a token names a key the desk doesn't hold, as it will after the provider rotates its keys. A key the provider doesn't publish raises `SignInError`.
- `person_from(client, keys, client_id=, client_secret=, redirect_uri=, pending=, answer=)` refuses an answer with an `error`, and one whose `state` isn't the pending sign-in's, before it sends anything. It exchanges the code at the token endpoint, with `grant_type=authorization_code`, the code, the redirect URI and the pending verifier, and the desk's id and secret by HTTP Basic authentication.
- It checks the ID token the token endpoint gives, with PyJWT: signed with RS256 by the key its header's `kid` names; issued by the provider; for the desk alone as its audience; not out of date; with `iss`, `sub`, `aud`, `exp`, `iat` and `nonce` all present; and with the pending sign-in's nonce. It gives a `Person` with the token's issuer and subject, and its email and name if it has them.
- Anything that fails raises `SignInError`.

```
Keys(client: httpx.AsyncClient, provider: Provider)
await keys.key(kid: str) -> jwt.PyJWK
await person_from(client, keys, *, client_id, client_secret, redirect_uri, pending, answer) -> Person
```

The tests sign people in at the scripted provider, which can give tokens of any shape in place of its own.
