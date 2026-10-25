`client.post(url, data=form, auth=(client_id, client_secret))` sends the form with HTTP Basic authentication.

---

`jwt.get_unverified_header(token)["kid"]` reads the key id from the token's header before anything is checked, so the right key can check it.

---

`jwt.decode(token, key, algorithms=["RS256"], audience=client_id, issuer=provider.issuer, options={"require": [...], "strict_aud": True})` checks the signature, the audience, the issuer and the expiry, and raises a subclass of `jwt.InvalidTokenError` when one fails.
