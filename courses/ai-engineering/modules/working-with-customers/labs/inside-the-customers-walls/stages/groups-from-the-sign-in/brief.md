Staff sign in through the office's own provider, which puts each person's groups in its directory into their ID token, as a `groups` claim: a list of names such as `"ssa-team"`. The office reads each of its directory's groups as one of its own, in `staff.py`'s `GROUPS`, and a directory group it doesn't list, such as a social club, gives no access at all.

`sign_in.py` and `tokens.py` are Signing in's, given: `discover` reads the provider's addresses, and `Keys` fetches its signing keys, again when a token names one it doesn't hold.

In `staff.py`, write `staff_from(keys, id_token, client_id)`, the `Staff` the token names: their subject, and the office's groups for the directory groups the token lists. The token checks out only when it's signed by one of the provider's keys, with RS256, for `client_id`, by the provider's issuer, and not expired, and holds `iss`, `sub`, `aud`, `exp` and `iat`; otherwise it raises `SignInError`. A token with no `groups` claim, or one that isn't a list, gives no groups, and an entry that isn't a name is left out.

```
staff_from(keys, id_token, client_id) -> Staff
```
