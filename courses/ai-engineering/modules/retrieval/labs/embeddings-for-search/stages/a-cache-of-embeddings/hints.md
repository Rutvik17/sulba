`hashlib.sha256(data).hexdigest()` gives the sha256 of some bytes in hexadecimal, and `text.encode()` a text's bytes in UTF-8.

---

`list(dict.fromkeys(texts))` keeps each text once, in the order it first comes.

---

`with connection:` commits what its block writes when the block ends, and `connection.executemany(sql, rows)` writes many rows in one call. `SELECT key, vector FROM vectors WHERE key IN (?, ?, ?)` finds the rows of three keys, given as parameters.
