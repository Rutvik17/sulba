`DELETE FROM sign_ins WHERE id = %s RETURNING ...` takes a row and gives it back in one statement, so two requests with the same token can't both take it.

---

`INSERT ... ON CONFLICT (issuer, subject) DO UPDATE SET email = EXCLUDED.email, name = EXCLUDED.name RETURNING id` adds a person or brings them up to date, and gives their id either way.

---

`now() + make_interval(days => %s)` is a time that many days from now, and `started_at > now() - make_interval(mins => %s)` is true of a row started within that many minutes.
