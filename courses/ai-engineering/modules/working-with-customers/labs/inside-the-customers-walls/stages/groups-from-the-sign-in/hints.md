`jwt.get_unverified_header(id_token)["kid"]` names the key to ask `keys.key` for. `jwt.decode` checks the signature, the audience, the issuer and the expiry when it's given the key, `algorithms`, `audience` and `issuer`, and `options={"require": [...]}` makes it refuse a token without a claim.

---

Every way a token can fail to check out raises a subclass of `jwt.InvalidTokenError`: catch that one and raise `SignInError` from it.
