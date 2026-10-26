`current_setting('app.student', true)` gives the setting, or null when it isn't set, so a policy `USING (student = current_setting('app.student', true))` matches no row without it. `CREATE ROLE` fails for a role that's there: in a `DO` block, `EXCEPTION WHEN duplicate_object THEN NULL` lets it pass.

---

`SET LOCAL ROLE` lasts until the transaction ends, and `SELECT set_config('app.student', %s, true)` sets the setting for the transaction alone, with the student as a parameter. Inside `with conn.transaction():`, both end with the block.
