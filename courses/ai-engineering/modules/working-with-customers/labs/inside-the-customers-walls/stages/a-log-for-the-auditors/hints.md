`hmac.new(key, subject.encode(), hashlib.sha256).hexdigest()` is the HMAC in hex.

---

A `datetime` that doesn't know its zone has a `utcoffset()` of `None`. `astimezone(UTC)` moves one that does to UTC.
