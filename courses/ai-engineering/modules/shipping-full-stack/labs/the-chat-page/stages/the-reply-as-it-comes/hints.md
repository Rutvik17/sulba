`body.getReader()` gives a reader whose `read()` resolves with `{ done, value }`, a chunk of bytes at a time. `new TextDecoder().decode(value, { stream: true })` keeps the start of a character whose bytes are cut until the next chunk, and `decode()` with nothing gives what's left at the end.

---

Keep the text that hasn't made a whole line yet, and add each chunk's text to it. A CR at the end of that text may be the first half of a CRLF, so wait for the next chunk before ending a line there, unless the stream has ended.

---

A generator's `finally` runs when the caller stops reading early, as `break` in a `for await` loop does, so `reader.cancel()` belongs there.
