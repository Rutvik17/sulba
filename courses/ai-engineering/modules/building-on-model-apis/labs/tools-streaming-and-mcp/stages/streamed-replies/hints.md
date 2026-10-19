`with client.stream("POST", "/chat/completions", json=body) as response:` keeps the response open while you read it, and `response.iter_bytes()` gives its bytes as they come. On an error, `response.read()` first, so `response.json()` has the body.

---

`response.iter_lines()` splits the text as `str.splitlines` does, at line breaks such as U+2028 too, which a reply's text can hold. `bytes.splitlines(keepends=True)` splits only at CR, LF and CR LF. A chunk can end partway through a line, or between a CR and its LF, so keep that last part until the next chunk.

---

Keep one tool call for each index, `calls.setdefault(index, {...})`, and add each piece of its name and arguments to what came before it.
