`HttpServer`'s docs, on `setExecutor`: with no executor, "a default implementation is used, which uses the thread which was created by the start() method."

---

`getRequestBody()` gives the same stream each time it's called, and a stream that's been read to its end has nothing left for the next reader.

---

An exchange whose reply has a length must be closed, or its body may never be sent.

---

A request goes to the context whose path is the longest prefix of its own. A request no context takes gets the server's own 404.
