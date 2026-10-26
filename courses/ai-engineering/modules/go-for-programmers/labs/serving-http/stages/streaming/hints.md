A `bufio.Scanner` over the body gives a line at a time. Its longest line is 64 kB unless you give it a buffer: `lines.Buffer(make([]byte, 64<<10), 1<<20)` takes lines up to a megabyte.

---

`strings.CutPrefix(line, "data:")`, then `strings.TrimPrefix(data, " ")`, reads the field with or without its space.

---

`http.NewResponseController(w).Flush()` sends what's been written so far. Set the headers before the first piece's write, and remember whether it has happened, since after it a failure can't change the status.
