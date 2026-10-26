A record's compact constructor, `public Ticket { ... }`, runs before the fields are set, and can give a parameter a new value: `summary = summary.strip();`.

---

`Objects.requireNonNull(service, "service")` throws a `NullPointerException` with the message `service` when `service` is `null`.

---

`@JsonProperty("ticket")` on the record's `id` component names it in JSON, and on each of `Status`'s constants, `@JsonProperty("open")` names the constant.

---

Jackson writes `isOpen()` as a field `open`, since its name makes it a getter. `@JsonIgnore` on the method leaves it out.
