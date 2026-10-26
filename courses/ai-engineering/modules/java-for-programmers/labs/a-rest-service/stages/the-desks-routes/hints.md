`exchange.getRequestURI().getPath()` gives the request's path, and `exchange.getRequestMethod()` its method, such as `GET`. A `Pattern` such as `/tickets/([^/]+)`, with `matcher(path).matches()`, matches the whole path, and `group(1)` gives the id.

---

Answer with `exchange.getResponseHeaders().set(...)` first, then `exchange.sendResponseHeaders(status, body.length)`, then write the body to `exchange.getResponseBody()`. `try (exchange) { ... }` closes the exchange however the handler ends.

---

`JSON.readValue(exchange.getRequestBody(), NewTicket.class)` reads the body into the record, and throws a `JacksonException`, which `Problems.of` turns into the right problem. `DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES` and `FAIL_ON_NULL_CREATOR_PROPERTIES` make the mapper refuse an unknown field and a missing one, and `@JsonFormat(pattern = "HH:mm")` on a record's `time` reads only hours and minutes.

---

`type.split(";", 2)[0].strip().equalsIgnoreCase("application/json")` reads a `Content-Type` such as `Application/JSON; charset=utf-8`.

---

`synchronized (desk) { ... }` lets one thread at a time into the block.
