`response.json()` gives the discovery document as a dict, and `document.get("code_challenge_methods_supported", [])` gives the methods it lists, or none.

---

`hashlib.sha256(verifier.encode("ascii")).digest()` is the verifier's SHA-256 as bytes, and `base64.urlsafe_b64encode(digest).rstrip(b"=")` writes it in base64url without padding.

---

`urllib.parse.urlencode(query)` writes a dict as a query string, with each value escaped.
