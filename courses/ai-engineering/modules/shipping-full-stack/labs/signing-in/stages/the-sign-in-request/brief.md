The desk is to sign its callers in with an OpenID provider, such as Google, rather than keep passwords of its own. Signing in starts with a request: the desk sends the browser to the provider, the person signs in there, and the provider sends the browser back to the desk with a code. In `sign_in.py`, write that request:

- `discover(client, issuer)` reads the provider's discovery document, at the issuer followed by `/.well-known/openid-configuration`, and gives a `Provider` with the issuer and the addresses the document gives for the authorization endpoint, the token endpoint and the keys, `jwks_uri`. It raises `SignInError` when the document can't be read, when its `issuer` isn't the issuer asked for, or when its `code_challenge_methods_supported` doesn't list `S256`.
- `Pending.new()` gives a sign-in on its way, with a new state, nonce and PKCE verifier, each 32 random bytes from `secrets.token_urlsafe(32)`.
- `pending.challenge` is the verifier's S256 code challenge: its SHA-256, in base64url without the `=` padding.
- `authorization_url(provider, client_id, redirect_uri, pending)` gives the address of the provider's authorization endpoint with the request in its query: `response_type=code`, the client id, the redirect URI, the scope `openid email profile`, the state, the nonce, the challenge and `code_challenge_method=S256`.

```
discover(client: httpx.AsyncClient, issuer: str) -> Provider
Pending.new() -> Pending
authorization_url(provider, client_id, redirect_uri, pending, scope="openid email profile") -> str
```

The tests sign people in at a scripted provider, `https://id.test`, which knows the desk as `desk`.
