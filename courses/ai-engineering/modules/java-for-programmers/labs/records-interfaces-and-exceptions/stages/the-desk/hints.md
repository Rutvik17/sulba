`new ArrayList<>(tickets)` copies a list, and `List.copyOf(tickets)` gives a copy no one can change. A map of maps needs each inner map and list copied too.

---

A `TreeSet<LocalTime>` keeps its times in order, however they were added.

---

`day.getDayOfWeek().getDisplayName(TextStyle.FULL, Locale.ENGLISH)` gives `Monday`, and a `LocalTime`'s `toString()` gives `09:00`.

---

`callbacks.remove(new Callback(ticket, day, time))` removes the callback equal to that one, since a record's `equals` compares its parts, and returns whether it found one.

---

`@JsonFormat(pattern = "HH:mm")` on the record's `time` component writes it as hours and minutes.
