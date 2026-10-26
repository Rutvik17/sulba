Your `record` gives `None` for a student the office doesn't have, and your `lines` words the rest.

---

`INSERT INTO tickets (student, question) VALUES (%s, %s)` writes a ticket, with its id and time from Postgres.
