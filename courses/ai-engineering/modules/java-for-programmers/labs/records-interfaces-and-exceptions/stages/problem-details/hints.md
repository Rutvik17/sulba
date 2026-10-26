`for (var each = error; each != null; each = each.getCause())` walks an error and its causes, outermost first.

---

A `switch` can test an object's type: `case Desk.Refused refused -> ...`. A case for a class must come before a case for its parent, or `javac` refuses it, as it does `catch` clauses in that order.

---

`getPath()` gives `JacksonException.Reference`s: `getPropertyName()` is a key, or `null` in an array, where `getIndex()` is the place.

---

A URI fragment holds letters, digits and `-._~!$&'()*+,;=:@/?` as they are. `text.getBytes(StandardCharsets.UTF_8)` gives the bytes to percent-encode the rest from, as `%C3%A9` for `é`.
